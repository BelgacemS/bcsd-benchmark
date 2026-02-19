import os
import json
from datetime import datetime

def generate_sample_metadata(sample_dir="data/sample"):
    if not os.path.exists(sample_dir):

        return

    for source_name in os.listdir(sample_dir):

        source_path = os.path.join(sample_dir, source_name)
        
        if not os.path.isdir(source_path):
            continue
            
        tasks = [d for d in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, d))]
        
        if not tasks:
            
            continue
            
        implementations = {"C": 0, "Cpp": 0, "Rust": 0, "Go": 0}
        
        for task in tasks:
            task_path = os.path.join(source_path, task)

            for lang in implementations.keys():
                lang_path = os.path.join(task_path, lang)

                if os.path.isdir(lang_path):
                    files = [f for f in os.listdir(lang_path) if os.path.isfile(os.path.join(lang_path, f))]
                    implementations[lang] += len(files)
        
        metadata = {

            "source": source_name,
            "scrape_date": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "implementations": implementations,
            "structure": f"<output_dir>/{source_name}/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>"
        }
        
        json_path = os.path.join(sample_dir, f"{source_name}_metadata.json")
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Fichier genere : {json_path}")


if __name__ == "__main__":
    generate_sample_metadata()