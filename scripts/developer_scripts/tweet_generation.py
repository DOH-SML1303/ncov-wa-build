import sys
import datetime
import pandas as pd

def bold(s):
    return('\033[1m' + s + '\033[0m')


# 0. Read excel sheet, read stored list of new labs ("new labs" list)
def read_excel_lab_file(table_file_name):
    excel_table = pd.read_excel(table_file_name, index_col=0, skiprows=1)
    excel_table = excel_table.fillna("empty?")
    lab_dictionary = {}
    for country, row in excel_table.iterrows():
        description = row["Who"]
        handle = row["Who to tag"]
        if country not in lab_dictionary:
            lab_dictionary[country] = {}
        if description in lab_dictionary[country]:
            print("Warning: lab description is found two times in excel table in same country (" + str(country) + ", " + str(description) + ")")
        lab_dictionary[country][description.lower()] = handle
    return lab_dictionary

### Optional: only if requested
# 1. Read metadata and collect submitting lab, originating lab and authors of all sequences within the specified month
#   - Also make a collection of all countries all time in order to detect newly appeared countries this month
#   - Return all labs of specified month & new countries
def read_metadata(filename, date_g, tweet):

    year_g = date_g[:4]
    month_g = date_g[5:7]

    if month_g == "12":
        year_gplus = str(int(year_g) + 1)
        month_gplus = "01"
    else:
        year_gplus = year_g
        month_gplus = str(int(month_g) + 1)
        if len(month_gplus) == 1:
            month_gplus = "0" + month_gplus

    countries_old = {"Africa": [], "Asia": [], "Europe": [], "North America": [], "Oceania": [], "South America": []}
    countries = {"Africa": [], "Asia": [], "Europe": [], "North America": [], "Oceania": [], "South America": []}
    labs_old = {"Africa": {}, "Asia": {}, "Europe": {}, "North America": {}, "Oceania": {}, "South America": {}}
    labs = {"Africa": {}, "Asia": {}, "Europe": {}, "North America": {}, "Oceania": {}, "South America": {}}

    new_seqs_count = 0

    with open(filename) as f:
        header = f.readline().split("\t")
        country_i = header.index("country")
        region_i = header.index("region")
        subm_date_i = header.index("date_submitted")
        sampl_date_i = header.index("date")
        subm_lab_i = header.index("submitting_lab")
        orig_lab_i = header.index("originating_lab")
        author_i = header.index("authors")

        line = f.readline()
        while line:
            l = line.split("\t")
            country = l[country_i]
            region = l[region_i]
            lab = l[subm_lab_i]
            orig_lab = l[orig_lab_i]
            author = l[author_i]
            date = l[subm_date_i]

            # Skip all entries with invalid dates
            if len(l[sampl_date_i]) != 10:
                line = f.readline()
                continue

            year = date[:4]
            month = date[5:7]

            # Collect all labs and countries from the specified month
            if year == year_g and month == month_g:
                new_seqs_count += 1
                if country not in countries[region]:
                    countries[region].append(country)
                    labs[region][country] = {"submitting_lab": [], "originating_lab": [], "authors": []}

                if lab not in labs[region][country]["submitting_lab"]:
                    labs[region][country]["submitting_lab"].append(lab)
                if orig_lab not in labs[region][country]["originating_lab"]:
                    labs[region][country]["originating_lab"].append(orig_lab)
                if author not in labs[region][country]["authors"]:
                    labs[region][country]["authors"].append(author)
            else:
                if tweet:
                    # Also check for next month in case we're late with tweeting
                    if month != month_gplus or year != year_gplus:

                        # Collect all old labs and countries
                        if country not in countries_old[region]:
                            countries_old[region].append(country)
                            labs_old[region][country] = {"submitting_lab": [], "originating_lab": [], "authors": []}

                        if lab not in labs_old[region][country]["submitting_lab"]:
                            labs_old[region][country]["submitting_lab"].append(lab)
                        if orig_lab not in labs_old[region][country]["originating_lab"]:
                            labs_old[region][country]["originating_lab"].append(orig_lab)
                        if author not in labs_old[region][country]["authors"]:
                            labs_old[region][country]["authors"].append(author)

            line = f.readline()

    new_countries = {}

    for region in countries:
        for country in countries[region]:
            if country not in countries_old[region]:
                if region not in new_countries:
                    new_countries[region] = []
                new_countries[region].append(country)

    return labs, labs_old, new_countries, new_seqs_count

# 2. Search twitter handles
#   - Only consider unknown handles or handles found in the "new labs" list
#   - Provide list of unknown labs to use for handle search
def collect_labs(labs, lab_dictionary, old):

    lab_collection = {}
    for region in labs:
        if region not in lab_collection:
            lab_collection[region] = {}
        for country in sorted(labs[region]):
            if country not in lab_collection[region]:
                lab_collection[region][country] = {}

            if data == "gisaid":
                for lab in labs[region][country]["submitting_lab"]: # Only consider submitting lab so far
                    # Handle known
                    if (country in lab_dictionary and lab.lower() in lab_dictionary[country]):
                        lab_collection[region][country][lab] = lab_dictionary[country][lab.lower()]
                        continue

                    # Handle unknown
                    if (country not in lab_dictionary or lab.lower() not in lab_dictionary[country]):
                        if not old:
                            lab_collection[region][country][lab] = "?"
                        continue

            if data == "open": # Needs special treatment due to many "?" labs and authors
                for lab_type in labs[region][country]: # iterate also over originating lab and authors
                    for lab in labs[region][country][lab_type]:
                        if lab == "?":
                            continue
                        # Handle known
                        if (country in lab_dictionary and lab.lower() in lab_dictionary[country]):
                            lab_collection[region][country][lab] = lab_dictionary[country][lab.lower()]
                            continue

                        # Handle unknown
                        if (country not in lab_dictionary or lab.lower() not in lab_dictionary[country]):
                            if not old:
                                lab_collection[region][country][lab] = "?"
                            continue

    lab_collection_clean = {}
    for region in lab_collection:
        for country in lab_collection[region]:
            if lab_collection[region][country] != {}:
                if region not in lab_collection_clean:
                    lab_collection_clean[region] = {}
                lab_collection_clean[region][country] = lab_collection[region][country]

    return lab_collection_clean

# 3. Manually by user: Browse for twitter handles
#   - If a handle is a different spelling of a known handle, just add to excel sheet
#   - If a handle is new, add to excel sheet & add to "new labs" list
#   - Update online version of excel sheet & upload "new labs" list to GitHub. This way, labs can be collected daily while storing knowledge of new labs until the end of the month
def print_labs(lab_collection):
    for region in lab_collection:
        for country in lab_collection[region]:
            s = country + ":\n"
            for lab in lab_collection[region][country]:
                if lab_collection[region][country][lab] == "?":
                    s += lab + ": ?\n"
            if s != country + ":\n":
                print(s)


# 4. Generate tweet if no unknown handles left
def generate_tweet(new_seqs_count, lab_collection, lab_collection_old, new_countries):
    known_handles = []
    for region in lab_collection_old:
        for country in lab_collection_old[region]:
            for lab in lab_collection_old[region][country]:
                if lab not in known_handles:
                    for handle in lab_collection_old[region][country][lab].split(", "):
                        known_handles.append(handle)

    tweet = []
    char_total = 260
    links = {
        "Africa": "nextstrain.org/ncov/gisaid/africa",
        "Asia": "nextstrain.org/ncov/gisaid/asia",
        "Europe": "nextstrain.org/ncov/gisaid/europe",
        "North America": "nextstrain.org/ncov/gisaid/north-america",
        "Oceania": "nextstrain.org/ncov/gisaid/oceania",
        "South America": "nextstrain.org/ncov/gisaid/south-america"
    }

    tweet.append("Thanks to #opendata sharing via @GISAID, we've updated nextstrain.org/ncov/gisaid with " + str(new_seqs_count) + " new #COVID19 #SARSCoV2 sequences during the last month!")

    if len(new_countries) > 0:
        countries = [country for region in new_countries for country in new_countries[region]]
        countries_links = [links[region] for region in new_countries]
        if len(countries) > 1:
            c = ", ".join(countries[:-1]) + " and " + countries[-1]
            l = ", ".join(countries_links[:-1]) + " and " + countries_links[-1]
        else:
            c = countries[0]
            l = countries_links[0]
        tweet.append("We have received our first sequences from " + c + ". Check them out on " + l + "!")

    # create simple list of all labs without duplicates
    labs = []
    for region in lab_collection:
        for country in lab_collection[region]:
            for lab in lab_collection[region][country]:
                for handle in lab_collection[region][country][lab].split(", "):
                    if handle == "?":
                        labs.append("???")
                    else:
                        if handle not in labs and handle not in known_handles:
                            labs.append(handle)

    t = "Thanks to all new submitters:\n\n" + labs[0]
    for i in range(1,len(labs)):
        if len(t) + len(labs[i]) <= char_total:
            t += ", " + labs[i]
        else:
            tweet.append(t)
            t = labs[i]
    tweet.append(t)

    with open(path_to_outputs + "tweet.txt", "w") as out:
        for i, t in enumerate(tweet):
            out.write(t + "\n\n" + str(i+1) + "/" + str(len(tweet)) + "\n\n\n")

# 5. End of the month: Purge "new labs" list, specify new month as input for 0.

path_to_metadata = "data/"
path_to_input = "scripts/developer_scripts/inputs_new_sequences/"
path_to_outputs = "scripts/developer_scripts/outputs_new_sequences/"
table_file_name = path_to_input + "Who to Tag in Nextstrain Update Posts COVID-19.xlsx"
gisaid_metadata = "downloaded_gisaid.tsv"
genbank_metadata = "metadata_genbank.tsv"

# Command line inputs:
#   -data: specify whether to use gisaid or open metadata (default: gisaid)
#   -date: specify month and year in the format YYYY-MM (default: current month)
#   -tweet: If present, will collect all labs to compare & find new labs and produce tweet
if __name__ == '__main__':
    data = "gisaid"
    date = str(datetime.datetime.now())[:7]
    tweet = False

    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "-data":
            data = args[i+1]
        if args[i] == "-date":
            date = args[i+1]
        if args[i] == "-tweet":
            tweet = True

    print("Processing " + bold(data) + " metadata for sequences from month " + bold(date) + ":")

    if data == "gisaid":
        metadata_filename = gisaid_metadata
    if data == "open":
        metadata_filename = genbank_metadata

    # 0. Read excel sheet, read stored list of new labs ("new labs" list)
    print("\n----------------------------------------------\n")
    print("Collecting list of twitter handles...")
    lab_dictionary = read_excel_lab_file(table_file_name)

    # 1.1 Read metadata and collect submitting lab, originating lab and authors of all sequences within the specified month
    ### Optional: Collect also all labs from the time before the specified month
    print("\n----------------------------------------------\n")
    print("Reading metadata...")
    labs, labs_old, new_countries, new_seqs_count = read_metadata(path_to_metadata + metadata_filename, date, tweet)

    if tweet:
        print("New countries added this month:")
        print(new_countries)

    # 2. Search twitter handles
    print("\n----------------------------------------------\n")
    print("Searching for labs...")
    lab_collection = collect_labs(labs, lab_dictionary, False)

    # 3. Manually by user: Browse for twitter handles
    print("\n----------------------------------------------\n")
    print("Proividing list of labs for manual search...")
    print_labs(lab_collection)


    ### Optional ###

    if tweet:

        # 2.2 Translate all old labs into handles
        print("\n----------------------------------------------\n")
        print("Searching for old labs...")
        lab_collection_old = collect_labs(labs_old, lab_dictionary, True)

        # 4. Generate tweet if no unknown handles left
        print("\n----------------------------------------------\n")
        print("Generating tweet...")
        generate_tweet(new_seqs_count, lab_collection, lab_collection_old, new_countries)
        print("New tweet written out to " + path_to_outputs + "tweet.txt")