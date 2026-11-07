"""Confined, immutable automated outputs with byte-identical resume support."""
from pathlib import Path
import pandas as pd
from .core import DATA
from .automated_protocol import AUTO_RESULTS,AUTO_DATA


def write_csv(path,rows,fields,*,root=None):
    path=Path(path).resolve()
    if root is not None:
        allowed=path.is_relative_to(Path(root).resolve())
    else:
        allowed=any(path.is_relative_to(p.resolve()) for p in [AUTO_RESULTS,AUTO_DATA])
        allowed=allowed or (path.name.startswith('automated') and any(path.parent==p.resolve() for p in [DATA/'source',DATA/'review',DATA/'frozen',DATA/'evaluation']))
    if not allowed:raise ValueError('Output outside automated namespace')
    content=pd.DataFrame(rows,columns=fields).to_csv(index=False,lineterminator='\n').encode('utf-8')
    if path.exists():
        if path.read_bytes()==content:return
        raise FileExistsError(f'Existing automated evidence differs: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle:handle.write(content)
