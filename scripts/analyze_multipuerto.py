#!/usr/bin/env python3
"""Analyze real Multipuerto flat files and map fields to spec."""
import csv
from pathlib import Path
import json

# Multipuerto specification (42 fields from PDF)
spec_42 = [
    "1. ID_Planilla",
    "2. Num_Plantacion", 
    "3. Codigo_Destino",
    "4. Codigo_Especie",
    "5. Codigo_Variedad",
    "6. Tipo_Produccion",
    "7. Codigo_Certificacion",
    "8. Numero_Puerto",
    "9. Fecha_Despacho",
    "10. Numero_Contenedor",
    "11. Cantidad_KG",
    "12. Codigo_Zona_Clima",
    "13. Codigo_Cosecha",
    "14. Codigo_Establecimiento",
    "15. Num_Lote",
    "16. Codigo_Tratamiento_Fitosanitario",
    "17. Codigo_Insecticida",
    "18. Concentracion_Ingrediente",
    "19. Duracion_Tratamiento",
    "20. Temperatura_Tratamiento",
    "21. Res_Muestreo1",
    "22. Res_Muestreo2",
    "23. Res_Muestreo3",
    "24. Res_Muestreo4",
    "25. Res_Muestreo5",
    "26. Codigo_Envase",
    "27. Codigo_Transporte",
    "28. Cantidad_Cajas",
    "29. Numero_Factura",
    "30. Num_Documento_Identidad",
    "31. Codigo_Importador",
    "32. Nombre_Contacto",
    "33. Codigo_Comision",
    "34. Codigo_Fundo",
    "35. Numero_Precinto",
    "36. Codigo_Tipo_Despacho",
    "37. Codigo_Phytosanitary_Cert",
    "38. Num_Dias_Transito",
    "39. Reservado",
    "40. Codigo_Pais_Destino",
    "41. Tipo_Representante",
    "42. Codigo_Exportador",
]

def main():
    data_dir = Path(__file__).resolve().parents[1] / 'data'
    multipuerto_files = list(data_dir.glob('Multipuerto_*.txt'))
    
    if not multipuerto_files:
        print('No Multipuerto files found.')
        return
    
    # Analyze each file
    analysis = {}
    for fpath in sorted(multipuerto_files):
        print(f'\n=== {fpath.name} ===')
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f'Total lines: {len(lines)}')
        
        # Parse first line as example
        line = lines[0].strip()
        fields = line.split(';')
        print(f'Total fields: {len(fields)}')
        print(f'Expected fields (PDF spec): {len(spec_42)}')
        
        # Print field mapping
        print('\nField mapping:')
        for i, (val, spec) in enumerate(zip(fields, spec_42)):
            print(f'  {i+1:2d}. {spec:40s} = "{val}"')
        
        if len(fields) > len(spec_42):
            print(f'\nExtra fields ({len(fields) - len(spec_42)}):')
            for i in range(len(spec_42), len(fields)):
                print(f'  {i+1:2d}. (extra) = "{fields[i]}"')
        
        analysis[fpath.name] = {
            'total_fields': len(fields),
            'sample_fields': fields,
            'lines': len(lines)
        }
    
    # Save analysis
    out_file = data_dir / 'multipuerto_analysis.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f'\n\nAnalysis saved to {out_file}')

if __name__ == '__main__':
    main()
