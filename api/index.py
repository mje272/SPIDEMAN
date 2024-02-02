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
    species_selection = request.form.getlist('species_selection')  # AKA genome project
    search_term = request.form['search_term']
    search_type = request.form['search_type']
    fit_on_screen = request.form['fit_on_screen']
    large_request = request.form['large_request']

    if large_request == "false":
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
        frequency_dict_list = request.form.getlist('frequency_dict_list') 
    
    
    # counts_list = [sum(x.values()) for x in frequency_dict_list]
    species_selection = ["asdg", "asdgas"]
    counts_list = [10, 122]

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


@app.route('/differential_enrichment', methods = ['POST'])
def differential_enrichment_graph():
    species_a = request.form['species_a']
    species_b = request.form['species_b']
    graph_enrichment_ratio = request.form['graph_enrichment_ratio']
    num_domains = int(request.form['num_domains'])
    include_ties = request.form['include_ties']

    col_a = mydb[species_a]
    col_b = mydb[species_b]

    domains_list_a = col_a.distinct('InterPro ID')

    dom_counts_dict_a = {}
    dom_counts_dict_b = {}
    dom_ratio_pairs = {}

    for domain in domains_list_a:
        dom_ct_a = col_a.count_documents({"InterPro ID": domain})
        dom_ct_b = col_b.count_documents({"InterPro ID": domain})
        dom_counts_dict_a[domain] = dom_ct_a
        dom_counts_dict_b[domain] = dom_ct_b
        dom_ratio_pairs[domain] = (dom_ct_a + 1) / (dom_ct_b + 1)

    dom_ratio_pairs = sorted(dom_ratio_pairs.items(), key=lambda x: x[1], reverse=True)
    if num_domains == 0:
        num_domains = len(dom_ratio_pairs)
    selected_dom_ratio_pairs = dom_ratio_pairs[:num_domains]
    i = num_domains
    if include_ties == "on" and num_domains < len(dom_ratio_pairs):  # 'and' clause to avoid index error
        while dom_ratio_pairs[i][1] == dom_ratio_pairs[num_domains-1][1]:
            selected_dom_ratio_pairs.append(dom_ratio_pairs[i])
            i += 1
            if i == len(dom_ratio_pairs):  # avoid index error if we've hit all the domains
                break
    selected_doms = [x[0] for x in selected_dom_ratio_pairs]
    dom_ratios = [x[1] for x in selected_dom_ratio_pairs]

    selected_counts_a = []
    selected_counts_b = []
    for dom in selected_doms:
        selected_counts_a.append(dom_counts_dict_a[dom])
        selected_counts_b.append(dom_counts_dict_b[dom])

    return render_template('differential_enrichment.html', species_a=species_a, species_b=species_b, domains=selected_doms, 
        frequency_a=selected_counts_a, frequency_b=selected_counts_b, ratios=dom_ratios, graph_enrichment_ratio=graph_enrichment_ratio)


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
