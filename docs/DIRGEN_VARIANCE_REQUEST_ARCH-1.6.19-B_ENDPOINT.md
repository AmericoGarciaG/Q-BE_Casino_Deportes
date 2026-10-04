# 📋 FICHA DE VARIANZA: ENDPOINT FOTMOB API 404 Y EXTRACCIÓN NEXT_DATA
**ID:** `VAR-HIST-ARCH-1.6.19-B`  
**ESTADO:** `RATIFICADO HISTÓRICO`  
**DESCRIPCIÓN:** El endpoint REST directo `https://www.fotmob.com/api/leagues?id={id}` respondió HTTP 404 en producción.  
**RESOLUCIÓN:** Se aplicó la técnica de extracción gobernada vía scraping del árbol pre-renderizado `__NEXT_DATA__` sobre la URL canónica `/overview/`, resolviendo la ingesta fáctica sin introducir datos sintéticos.
