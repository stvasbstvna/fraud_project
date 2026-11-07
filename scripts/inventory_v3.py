from pathlib import Path
import csv
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
paths = sorted((root / 'results/benchmark_v3/final_run/figures').glob('*.png'))
sheet = Image.new('RGB', (1600, 1250), 'white')
for i, p in enumerate(paths):
    sheet.paste(ImageOps.contain(Image.open(p).convert('RGB'), (800, 250)), ((i % 2)*800, (i // 2)*250))
sheet.save(root / 'results/benchmark_v3/final_run/figure_contact_sheet.png')
files = sorted(p for d in ['configs','data','docs','models','results','src','tests']
               for p in (root/d/'benchmark_v3').rglob('*')
               if p.is_file() and '__pycache__' not in p.parts and 'cache_guard' not in str(p)
               and p.name != 'ADDED_FILES.csv')
files += [root/'scripts/finalize_v3_docs.py', root/'scripts/inventory_v3.py']
with (root/'docs/benchmark_v3/ADDED_FILES.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['path','bytes'])
    w.writerows((p.relative_to(root).as_posix(), p.stat().st_size) for p in sorted(files))
print(len(files), 'v3 artifacts inventoried')
