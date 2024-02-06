from flask import Flask, request, render_template
import requests
import json
#INSTRUCTIONS/USAGE DETAILS
# can only do one domain id, but multiple domains may show up from key word searches
#   description must contain exact string entered (case insensitive though)
# technically, species=genome project (ie, multiple genome projects actually represent same species)
# if no InterPro domain entered, will query all entries (will interpret as blank string keyword search)
    # produces histogram showing number of entries for each species

# for differential enrichment plot, enter 0 to graph all of species A
# note that it does matter which species is A vs B
# for ties in level of differential enrichment, it will rank alphabetically ie IPR00157>IPR002542>IPR03665 (I think)


app = Flask(__name__)

@app.route('/')
def index():

    return render_template('index.html')
    

@app.route('/generate_histogram', methods = ['POST'])
def generate_histogram():  
    search_term = request.form['search_term']
    search_type = request.form['search_type']
    fit_on_screen = request.form['fit_on_screen']
    large_request = request.form['large_request']

    if large_request == "false":
        species_selection = request.form.getlist('species_selection')  # AKA genome project

        url = "https://dmn7mpvpxwkf3r4yvwb4abbcry0nzlqj.lambda-url.us-west-1.on.aws/"
        data = json.dumps({
            "species_selection": species_selection,
            "search_term": search_term,
            "search_type": search_type
            })
        headers = {"Content-Type": "application/json"}
        r = requests.post(url=url, data=data, headers=headers) 
        frequency_dict_list = r.json()
    else:
        species_selection = json.loads(request.form['species_selection'])  # AKA genome project
        frequency_dict_list = json.loads(request.form['frequency_dict_list'])
    
    
    counts_list = [sum(x.values()) for x in frequency_dict_list]
    # species_selection = ["asdg", "asdgas"]
    # counts_list = [5 for x in species_selection]

    return render_template('histogram.html', species_list=species_selection, counts_list=counts_list, fit_on_screen=fit_on_screen, search_term=search_term, frequency_dict_list=frequency_dict_list)

@app.route('/histogram_large_request', methods = ['POST'])
def histogram_large_request():
    species_selection = request.form.getlist('species_selection')  # AKA genome project
    search_term = request.form['search_term']
    fit_on_screen = request.form['fit_on_screen']
    url = 'https://heqmgl4nsbb42yleftbayog6im0qwrep.lambda-url.us-west-1.on.aws/'
    data = json.dumps({
        "search_term": search_term,
        })
    headers = {"Content-Type": "application/json"}
    r = requests.post(url=url, data=data, headers=headers)
    domains_of_interest = r.json()
    return render_template('histogram_loading_page.html', species_list=species_selection, fit_on_screen=fit_on_screen, search_term=search_term, domains_of_interest=domains_of_interest)
    
#@app.route('/generate_large_histogram', methods = ['POST'])  # maybe make this gettable
#def generate_large_histogram():
#    species_selection
#    return render_template('histogram.html') 


@app.route('/load_differential_enrichment', methods = ['POST'])
def load_differential_enrichment_graph():


    species_a = request.form['species_a']
    species_b = request.form['species_b']
    graph_enrichment_ratio = request.form['graph_enrichment_ratio']
    num_domains = int(request.form['num_domains'])
    include_ties = request.form['include_ties']

    return render_template('differential_enrichment_loading_page.html', species_a=species_a, species_b=species_b, graph_enrichment_ratio=graph_enrichment_ratio, num_domains=num_domains, include_ties=include_ties)
    

@app.route('/differential_enrichment', methods = ['POST'])
def render_differential_enrichment_graph():
    species_a = request.form['species_a']
    species_b = request.form['species_b']
    domains = request.form['domains']
    frequency_a = request.form['frequency_a']
    frequency_b = request.form['frequency_b']
    ratios = request.form['ratios']
    graph_enrichment_ratio = request.form['graph_enrichment_ratio']
    raw_data = request.form['raw_data']

    return render_template('differential_enrichment.html', species_a=species_a, species_b=species_b, domains=domains, frequency_a=frequency_a, frequency_b=frequency_b, ratios=ratios, graph_enrichment_ratio=graph_enrichment_ratio, raw_data=raw_data) 

species_options_list = []
@app.route('/get_species_list_options')
def get_species_list_options():  # use this to create options for permanent update of selection menu  ### doesn't work online, but could adapt it to
    collection = mydb["254_species_data_alphabetized"].find({}, {"Genome project": 1})
    for i in collection:
        species = i["Genome project"]
        option = f"<option value={species}>{species}</option>"
        if not option in species_options_list:
            species_options_list.append(option)
    return species_options_list

if __name__ == "__main__":
    app.run(debug = True)
