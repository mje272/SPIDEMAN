from flask import Flask, request, render_template, url_for
import pymongo
from timeit import default_timer as timer

#INSTRUCTIONS/USAGE DETAILS
# can only do one domain id, but multiple domains may show up from key word searches
#   description must contain exact string entered (case insensitive though)
# technically, species=genome project (ie, multiple genome projects actually represent same species)
# if no InterPro domain entered, will query all entries (will interpret as blank string keyword search)
    # produces histogram showing number of entries for each species

# for differential enrichment plot, enter 0 to graph all of species A
# note that it does matter which species is A vs B
# for ties in level of differential enrichment, it will rank alphabetically ie IPR00157>IPR002542>IPR03665 (I think)


myclient = pymongo.MongoClient("mongodb://localhost:27017")
mydb = myclient["URAP_254_species_db"]
# mycol = mydb["254_species_data"]


app = Flask(__name__)

@app.route('/')
def index():

    return render_template('index.html')
    # collection = mycol.find({}, {"Genome project": 1})
    # for i in collection:
    #     species = i["Genome project"]
    #     if not species in species_options_list:
    #         species_options_list.append(species)
    # return render_template('index.html', species_options_list=species_options_list)
    ######### ^Use if selection list has not been updated in index.html (see index.html) ###########
    ######### works slowly, but will generate selection list automatically

@app.route('/generate_histogram', methods = ['POST'])
def generate_histogram():  
    species_selection = request.form.getlist('species_selection')  # AKA genome project
    interpro_domain = request.form['interpro_domain']
    fit_on_screen = request.form['fit_on_screen']
   
    species_domain_count = {}

    t1 = timer()
    for species in species_selection:
        one_species_col = mydb[species]

        count = one_species_col.count_documents({"$or": [{"InterPro ID": interpro_domain}, {"InterPro description": {"$regex": f"({interpro_domain})+", '$options': 'i'}}]})
        species_domain_count[species] = count
    t2 = timer()
    
    print(f"took {t2-t1} seconds to get data")    

    return render_template('histogram.html', x_vals=list(species_domain_count.keys()), y_vals=list(species_domain_count.values()), fit_on_screen=fit_on_screen, interpro_domain=interpro_domain)


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
    # domains_list_a = domains_list_a[:5]    # remember to remove this
    t1 = timer()
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

    t2 = timer()
    print(f"That took {t2-t1} seconds")

    return render_template('differential_enrichment.html', species_a=species_a, species_b=species_b, domains=selected_doms, 
        frequency_a=selected_counts_a, frequency_b=selected_counts_b, ratios=dom_ratios, graph_enrichment_ratio=graph_enrichment_ratio)


species_options_list = []
@app.route('/get_species_list_options')
def get_species_list_options():  # use this to create options for permanent update of selection menu
    collection = mydb["254_species_data_alphabetized"].find({}, {"Genome project": 1})
    for i in collection:
        species = i["Genome project"]
        option = f"<option value={species}>{species}</option>"
        if not option in species_options_list:
            species_options_list.append(option)
    return species_options_list

if __name__ == "__main__":
    app.run(debug = True)