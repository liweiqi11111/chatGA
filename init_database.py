from server.knowledge_base.migrate import create_tables, folder2db, recreate_all_vs, list_kbs_from_folder
from configs.model_config import NLTK_DATA_PATH, KB_ROOT_PATH
import nltk
import os
nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.formatter_class = argparse.RawTextHelpFormatter

    parser.add_argument(
        "--recreate-vs",
        action="store_true",
        help=('''
            recreate all vector store.
            use this option if you have copied document files to the content folder, but vector store has not been populated or DEFAUL_VS_TYPE/EMBEDDING_MODEL changed.
            if your vector store is ready with the configs, just skip this option to fill info to database only.
            '''
        )
    )
    args = parser.parse_args()

    create_tables()
    print("database talbes created")

    if args.recreate_vs:
        print("recreating all vector stores")
        recreate_all_vs()
    else:
        print("filling kb infos to database")
        for f in os.listdir(KB_ROOT_PATH):
            if not os.path.isdir(os.path.join(KB_ROOT_PATH, f)):
                continue
            user_id = int(f)
            for kb in list_kbs_from_folder(user_id):
                folder2db(user_id, kb, "fill_info_only")
