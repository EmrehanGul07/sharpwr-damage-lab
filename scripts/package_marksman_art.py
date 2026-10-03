"""Package original GLBs, catalogue and runtime for reuse."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
def package():
    path=ROOT/'assets/marksman-3d/sharpwr-marksman-art-v1.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for model in sorted((ROOT/'assets/marksman-3d/models').glob('*.glb')):
            archive.write(model,'models/'+model.name)
        for item in ('data/marksman-3d-assets.json','data/marksman-art-direction.json','docs/marksman-art-v1.md'):
            source=ROOT/item;archive.write(source,source.name)
        for item in ('rig.js','effects.js','rift-arena.js','scene.js','practice.js','combat-hud.js'):
            archive.write(ROOT/'assets/marksman-3d'/item,'runtime/'+item)
    return path
if __name__=='__main__':print(package())
