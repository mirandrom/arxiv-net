"""
Checks the references/citations of papers in our database
If these papers aren't there, collects them
"""

import pickle
from tqdm import tqdm
from arxiv_net.ss import semantic_scholar_api as ss
from arxiv_net.utilities import Config, safe_pickle_dump

if __name__ == "__main__":
    # lets load the existing ss database to memory
    try:
        ss_db = pickle.load(open(Config.ss_ref_db_path, 'rb'))

        print('database has %d entries at start' % (len(ss_db),))
        num_added_total = 0
        num_just_added = 0
        num_previous_added_total = 0
        for parent_id in tqdm(list(ss_db.keys()).copy()):
            ss_data_parent = ss_db[parent_id]
            # Check citations
            for citation in ss_data_parent.citations:
                citation_id = citation.arxivId
                if citation_id is not None and citation_id not in ss_db:
                    ss_data = ss.get_data(citation_id)
                    if ss_data is not None:
                        ss_db[citation_id] = ss_data
                        num_added_total += 1

            # Check references
            for reference in ss_data_parent.references:
                ref_id = reference.arxivId
                if ref_id is not None and ref_id not in ss_db:
                    ss_data = ss.get_data(ref_id)
                    if ss_data is not None:
                        ss_db[ref_id] = ss_data
                        num_added_total += 1

            if num_just_added != num_added_total:
                print('Found ', num_added_total - num_just_added)
                num_just_added = num_added_total

            # Save database every 100 papers
            if num_previous_added_total + 100 < num_added_total:
                num_previous_added_total += 100
                print('Added: ', num_added_total)
                print(
                    'Saving database with %d papers to %s' % (
                        len(ss_db), Config.ss_ref_db_path))
                safe_pickle_dump(ss_db, Config.ss_ref_db_path)

        # Save when finished
        print('Added: ', num_added_total)
        print(
            'Saving database with %d papers to %s' % (
                len(ss_db), Config.ss_ref_db_path))
        safe_pickle_dump(ss_db, Config.ss_ref_db_path)

    except Exception as e:
        print('Error:')
        print(e)

