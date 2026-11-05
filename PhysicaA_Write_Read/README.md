# Writing, retention and dynamical readout of group memory

This is a partial source mirror for the writing--readout study. It contains the recovered figure-generation scripts, mechanism definitions, manuscript build script, SVG icons, dependency list and a recovery utility. The full simulator and analysis code are in the complete replication archive and are not yet all mirrored in this branch.

The complete archive originally assembled for Zenodo is `PhysicaA_Zenodo_Code_Data_20261105.zip` (61,202,702 bytes; SHA-256 `9c7e001d81acdfa9b147d8587eb7144bff35f15bd47e4f3f16e4a02a086bf642`). It includes the complete simulator and analysis, all saved results and the 64 inputs needed by the locked strength analysis. That archive passed a clean from-data reproduction before the workspace became unavailable.

For the earlier saved file `PhysicaA_Code_Data_Write_Read.zip` (SHA-256 `d247bdebb1af487880ebb2357dd1f66cb24849a07af358720f681f02efca9ed2`), the included `restore_zenodo_archive.py` reconstructs the 64 missing inputs from the saved merged arrays and checks all 102 original result hashes. It writes a separate archive and does not change the input. The utility passed an automated synthetic-data smoke test.

Usage with Python and NumPy installed:

```text
python restore_zenodo_archive.py /path/to/PhysicaA_Code_Data_Write_Read.zip
```

The result is `PhysicaA_Zenodo_Code_Data_Recovered.zip`. The utility checks its ZIP integrity, all original-result hashes and all recovered loss/dose arrays. The full archived release contains the inputs, fonts and manuscript sources needed by `python reproduce.py --from-data`.
