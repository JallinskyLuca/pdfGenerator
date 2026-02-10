from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime, timedelta
import os

# DATOS PREDETERMINADOS 
EMPRESA_NOMBRE = "TU EMPRESA S.A."
EMPRESA_DIRECCION = "Calle Falsa 123, Ciudad"
EMPRESA_MAIL = "contacto@tuempresa.com"
EMPRESA_TELEFONO = "+54 11 1234-5678"
IVA_PORCENTAJE = 0.21

# Agregamos el parámetro tipo_doc con valor por defecto
def generar_presupuesto_moderno(num, fecha_str, cliente, direccion, mail, pago, items, comentarios, tipo_doc="PRESUPUESTO"):
    fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
    vencimiento = (fecha_dt + timedelta(days=30)).strftime("%d/%m/%Y")
    
    # Nombre de archivo dinámico
    archivo = f"{tipo_doc}_{num}_{cliente.replace(' ', '_')}.pdf"
    c = canvas.Canvas(archivo, pagesize=A4)
    ancho, alto = A4

    # COLOR DINÁMICO: Verde para Recibo, Azul para Presupuesto
    color_corp = colors.Color(0.15, 0.55, 0.3) if tipo_doc == "RECIBO" else colors.Color(0.2, 0.4, 0.7)
    
    # HEADER DINÁMICO
    c.setFillColor(color_corp)
    c.rect(0, alto - 4*cm, ancho, 4*cm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 30)
    # Título dinámico según la elección
    c.drawString(1.5*cm, alto - 2.5*cm, tipo_doc.upper())

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(ancho - 1.5*cm, alto - 1.5*cm, EMPRESA_NOMBRE)
    c.setFont("Helvetica", 9)
    c.drawRightString(ancho - 1.5*cm, alto - 2*cm, EMPRESA_DIRECCION)
    c.drawRightString(ancho - 1.5*cm, alto - 2.4*cm, EMPRESA_MAIL)
    c.drawRightString(ancho - 1.5*cm, alto - 2.8*cm, EMPRESA_TELEFONO)

    # BLOQUES GRISES SUPERIORES 
    c.setFillColor(colors.Color(0.95, 0.95, 0.95))
    c.rect(1.5*cm, alto - 8.2*cm, 8*cm, 3.5*cm, fill=1, stroke=0) 
    c.rect(10.5*cm, alto - 8.2*cm, 9*cm, 3.5*cm, fill=1, stroke=0)  

    c.setFillColor(colors.black)
    y_inicio_texto = alto - 5.6*cm
    sep = 0.7*cm
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.8*cm, y_inicio_texto, "FECHA EMISIÓN:")
    c.drawString(1.8*cm, y_inicio_texto - sep, f"N° {tipo_doc}:") # Texto dinámico
    c.drawString(1.8*cm, y_inicio_texto - (sep*2), "VENCIMIENTO:")

    c.setFont("Helvetica", 9)
    c.drawString(5.5*cm, y_inicio_texto, fecha_str)
    c.drawString(5.5*cm, y_inicio_texto - sep, f"{num:04d}")
    c.drawString(5.5*cm, y_inicio_texto - (sep*2), vencimiento)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(10.8*cm, y_inicio_texto, "CLIENTE:")
    c.drawString(10.8*cm, y_inicio_texto - sep, "DIRECCIÓN:")
    c.drawString(10.8*cm, y_inicio_texto - (sep*2), "MAIL:")
    c.drawString(10.8*cm, y_inicio_texto - (sep*3), "MÉTODO PAGO:")

    c.setFont("Helvetica", 9)
    c.drawString(13.8*cm, y_inicio_texto, cliente)
    c.drawString(13.8*cm, y_inicio_texto - sep, direccion)
    c.drawString(13.8*cm, y_inicio_texto - (sep*2), mail)
    c.drawString(13.8*cm, y_inicio_texto - (sep*3), pago)

    # TABLA DE ITEMS (CON COLUMNA DE CATEGORÍA)
    y_t = alto - 9.5*cm 
    c.setFillColor(color_corp)
    c.rect(1.5*cm, y_t, ancho - 3*cm, 0.8*cm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(1.7*cm, y_t + 0.3*cm, "CATEGORÍA")
    c.drawString(4.0*cm, y_t + 0.3*cm, "CANT.")
    c.drawString(5.5*cm, y_t + 0.3*cm, "DESCRIPCIÓN")
    c.drawRightString(ancho - 5.5*cm, y_t + 0.3*cm, "P. UNITARIO")
    c.drawRightString(ancho - 1.7*cm, y_t + 0.3*cm, "TOTAL")

    y_fila = y_t - 0.7*cm
    subtotal = 0
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)

    for item in items:
        total_item = item['cant'] * item['precio']
        subtotal += total_item
        cat = item.get('cat', 'Otros') # Obtenemos la categoría del ítem
        
        c.drawString(1.7*cm, y_fila, cat)
        c.drawString(4.0*cm, y_fila, str(item['cant']))
        c.drawString(5.5*cm, y_fila, item['desc'])
        c.drawRightString(ancho - 5.5*cm, y_fila, f"$ {item['precio']:,.2f}")
        c.drawRightString(ancho - 1.7*cm, y_fila, f"$ {total_item:,.2f}")
        
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(1.5*cm, y_fila - 0.2*cm, ancho - 1.5*cm, y_fila - 0.2*cm)
        y_fila -= 0.8*cm
        
    # TOTALES 
    iva = subtotal * IVA_PORCENTAJE
    total_gral = subtotal + iva

    y_fila -= 0.5*cm
    c.setFont("Helvetica", 10)
    c.drawRightString(ancho - 5.5*cm, y_fila, "SUBTOTAL:")
    c.drawRightString(ancho - 1.7*cm, y_fila, f"$ {subtotal:,.2f}")
    
    y_fila -= 0.6*cm
    c.drawRightString(ancho - 5.5*cm, y_fila, f"IVA ({int(IVA_PORCENTAJE*100)}%):")
    c.drawRightString(ancho - 1.7*cm, y_fila, f"$ {iva:,.2f}")

    y_fila -= 1*cm
    c.setFillColor(color_corp)
    c.rect(ancho - 8.5*cm, y_fila - 0.3*cm, 7*cm, 1*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(ancho - 8.2*cm, y_fila + 0.1*cm, "TOTAL:")
    c.drawRightString(ancho - 1.7*cm, y_fila + 0.1*cm, f"$ {total_gral:,.2f}")

    # DATOS DE PAGO Y FIRMA
    y_inferior = 6*cm 
    
    # Bloque de Datos Bancarios
    c.setFillColor(colors.Color(0.97, 0.97, 0.97))
    c.rect(1.5*cm, y_inferior, 8*cm, 2.5*cm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.8*cm, y_inferior + 2*cm, "DATOS PARA TRANSFERENCIA:")
    c.setFont("Helvetica", 8)
    c.drawString(1.8*cm, y_inferior + 1.5*cm, "Banco: Banco Nación")
    c.drawString(1.8*cm, y_inferior + 1.1*cm, "CBU: 0110123456789012345678")
    c.drawString(1.8*cm, y_inferior + 0.7*cm, "Alias: TU.EMPRESA.OK")

    # Área de Firmas
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(11*cm, y_inferior + 1.2*cm, 14.5*cm, y_inferior + 1.2*cm)
    c.drawCentredString(12.75*cm, y_inferior + 0.7*cm, "Firma Empresa")
    c.line(15.5*cm, y_inferior + 1.2*cm, 19*cm, y_inferior + 1.2*cm)
    c.drawCentredString(17.25*cm, y_inferior + 0.7*cm, "Firma Cliente")

    # CONDICIONES FINALES 
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm, 3.5*cm, "COMENTARIOS:")
    c.setFont("Helvetica", 8)
    c.drawString(1.5*cm, 3*cm, comentarios if comentarios else "Sin comentarios adicionales.")
    
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm, 2.2*cm, "CONDICIÓN DE PAGO:")
    c.setFont("Helvetica", 8)
    # Ajustamos texto de vencimiento según el tipo de documento
    condicion_texto = "Pago realizado al contado." if tipo_doc == "RECIBO" else "Válido por 30 días."
    c.drawString(1.5*cm, 1.7*cm, condicion_texto)

    c.save()