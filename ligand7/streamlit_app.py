import streamlit as st
import sys 
import pandas as pd
import os
import json
from pprint import pprint

from ligand7 import __version__ as ligand7_version
from ligand7.predict.pubchem import get_inchiKey
from ligand7.predict.chemical2enzymes import chem2enzymes
from ligand7.predict.enzymes2operons import append_operons, pull_regulators

def setup_page():
    st.set_page_config(page_title="Ligand7", layout='centered', initial_sidebar_state='auto')
    sys.tracebacklimit = 0 #removes traceback so code is not shown during errors

    hide_streamlit_style = '''
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    '''

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.markdown(f'<div style="text-align: right; font-size: 0.9em"> {ligand7_version} </div>', unsafe_allow_html=True)

    st.subheader('Predict sensors responsive to an input ligand')
    sidebar = st.sidebar.empty()

    #this removes the full-screen button for various elements
    style_fullscreen_button_css = """
        button[title="View fullscreen"] {
            display: none;
        }
        button[title="View fullscreen"]:hover {
            display: none;
            }
        """
    st.markdown(
        "<style>"
        + style_fullscreen_button_css
        + "</styles>",
        unsafe_allow_html=True,
    )

def make_clickable(text):
    # target _blank to open new window
    # extract clickable text to display for your link
    link = "https://www.ncbi.nlm.nih.gov/protein/"+str(text)
    return f'<a target="_blank" href="{link}">{text}</a>'


def display_data(regulators):

    for i in range(0, len(regulators)):
        with st.expander(regulators[i]["refseq"]):

            reg = regulators[i]["protein"]



                #Sensor info
            sensor = [
                        "https://www.ncbi.nlm.nih.gov/protein/"+str(regulators[i]["refseq"]), 
                        regulators[i]["annotation"],
                        ", ".join(reg["organism"])[:-2] 
                    ]
            sensor_columns = ["RefSeq link", "Annotation",  "Organism"]

            s_df = pd.DataFrame(sensor, index= sensor_columns)
            s_df.columns = ["Regulator information"]

            st.dataframe(s_df, width=700)



                #Enzyme info
            enzyme = [
                        regulators[i]["equation"],
                        regulators[i]["rhea_id"], 
                        reg["enzyme"]["description"],
                        "https://www.uniprot.org/uniprotkb/"+str(reg["enzyme"]["uniprot_id"])
                        ]
            enzyme_columns = ["Reaction", "Rhea ID", "Annotation", "Uniprot link"]

            for ref in range(0,len(reg["enzyme"]["dois"])):
                link = "https://doi.org/"+str(reg["enzyme"]["dois"][ref])
                text = "Reference "+str(ref+1)
                enzyme.append(link)
                enzyme_columns.append(text)

            e_df = pd.DataFrame(enzyme, index= enzyme_columns)
            e_df.columns = ["Enzyme information"]
            st.dataframe(e_df, width=700)


            alt_ligands = [lig for lig in regulators[i]["alt_ligands"]]
            l_df = pd.DataFrame(alt_ligands, columns=["Alternative ligand name"])
            st.dataframe(l_df, width=700)






def run_streamlit():

    setup_page()

    
    with st.form("my_form"):
        chemical_name = st.text_input("Chemical name", "Isovalerate")
        InChiKey = get_inchiKey(str(chemical_name), "name")
        # print(chemical_name)
        # print(InChiKey)
        domain_filter = "Bacteria"
        lineage_filter_name = st.select_slider("Domain filter stringency", options=["Domain", "Phylum", "Class", "Order", "Family", "None"], value="Family")
        reviewed = st.checkbox("Reviewed?", value=True)


        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.spinner("Processing")
            my_bar = st.progress(0, text="Fetching enzymes ...")

            st.write("InchiKey: "+str(InChiKey))
            
            if os.path.exists("./ligand7/temp/"+str(chemical_name)+".json"):
                with open("./ligand7/temp/"+str(chemical_name)+".json", "r") as f:
                    regulators = json.load(f)
                    print("loaded cached reg data")

                    display_data(regulators)

            else:

                data = chem2enzymes(InChiKey = InChiKey,
                    domain_filter = domain_filter,
                    lineage_filter_name = lineage_filter_name, 
                    reviewed_bool = reviewed)

                my_bar.progress(40, text="Fetching operons ...")

                data = append_operons(data, chemical_name)

                my_bar.progress(95, text="Fetching regulators ...")


                if data == None:
                    st.write("No regulators found")
                
                else:

                    regulators = pull_regulators(data, chemical_name)
                    
                    with open("./ligand7/temp/"+str(chemical_name)+".json", "w+") as f:
                        f.write(json.dumps(regulators))
                        print("cached regulator data")


                    if regulators == None or len(regulators) == 0:
                        st.write("No regulators found")


                    else:
                        display_data(regulators)


                    
            my_bar.progress(100, text="Complete.")

