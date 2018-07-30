for /l %%x in (40, -1, 1) do (
   mkdir %%x
   move *%%xof40.jpeg "G:\Aharon\SCANS\unknown beetle 40 r 3 z\%%x"
   cd %%x
   mkdir -1000
   move *-1000R%%xof40.jpeg "G:\Aharon\SCANS\unknown beetle 40 r 3 z\%%x\-1000"
   mkdir 1000
   move *1000R%%xof40.jpeg "G:\Aharon\SCANS\unknown beetle 40 r 3 z\%%x\1000"
   mkdir 2000
   move *2000R%%xof40.jpeg "G:\Aharon\SCANS\unknown beetle 40 r 3 z\%%x\2000"
   mkdir 0
   move *0R%%xof40.jpeg "G:\Aharon\SCANS\unknown beetle 40 r 3 z\%%x\0"
   cd ..
)
pause