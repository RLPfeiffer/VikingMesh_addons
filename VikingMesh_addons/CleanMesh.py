import pymeshlab
import os
import sys
ms = pymeshlab.MeshSet()


importDirectory = sys.argv[1]
exportDirectory = sys.argv[2]
files=[]

 
for filename in os.listdir(importDirectory):
    f = os.path.join(importDirectory, filename)
    if filename.startswith('Morphology') and filename.endswith('.dae'):
        files.append(f)
        
        
for f in files:
    ms.load_new_mesh(f)
    ms.generate_surface_reconstruction_screened_poisson(depth=10, preclean = True)
    ms.save_current_mesh(os.path.join(exportDirectory, os.path.basename(f)))
    if not os.path.isdir(exportDirectory):
        os.mkdir(exportDirectory)