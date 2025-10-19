from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Dict, Any, List
import io
import os

class PDFService:
    """Servicio para generar PDFs de cierres de caja"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
    
    def generate_cash_closure_pdf(self, closure_data: Dict[str, Any], items_data: Dict[str, Any], user_name: str) -> bytes:
        """Genera un PDF del cierre de caja con items vendidos"""
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Validar datos de entrada
            if not closure_data:
                raise ValueError("Datos del cierre de caja no pueden estar vacíos")
            
            if not user_name:
                user_name = "Usuario Desconocido"
            
            # Crear el contenido del PDF
            story = []
            
            # Título principal
            story.append(Paragraph("CIERRE DE CAJA", self.styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            # Información del cierre
            story.extend(self._create_closure_info_section(closure_data, user_name))
            story.append(Spacer(1, 20))
            
            # Resumen de ventas
            story.extend(self._create_sales_summary_section(closure_data))
            story.append(Spacer(1, 20))
            
            # Desglose por método de pago
            story.extend(self._create_payment_breakdown_section(closure_data))
            story.append(Spacer(1, 20))
            
            # Conteo físico y diferencias
            story.extend(self._create_physical_count_section(closure_data))
            story.append(Spacer(1, 20))
            
            # Items vendidos
            if items_data and items_data.get('items_sold'):
                story.extend(self._create_items_sold_section(items_data))
                story.append(Spacer(1, 20))
            
            # Notas
            if closure_data.get('notes'):
                story.extend(self._create_notes_section(closure_data))
            
            # Construir el PDF
            doc.build(story)
        
            # Obtener el contenido del buffer
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            # Cerrar el buffer en caso de error
            if 'buffer' in locals():
                buffer.close()
            raise Exception(f"Error generando PDF: {str(e)}")
    
    def _create_closure_info_section(self, closure_data: Dict[str, Any], user_name: str) -> List:
        """Crea la sección de información del cierre"""
        elements = []
        
        elements.append(Paragraph("INFORMACIÓN DEL CIERRE", self.styles['CustomHeading']))
        
        # Tabla de información
        info_data = [
            ['Usuario:', user_name],
            ['Fecha:', closure_data.get('shift_date', 'N/A')],
            ['Inicio del Turno:', closure_data.get('shift_start', 'N/A')],
            ['Fin del Turno:', closure_data.get('shift_end', 'N/A')],
            ['Estado:', closure_data.get('status', 'N/A')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        elements.append(info_table)
        return elements
    
    def _create_sales_summary_section(self, closure_data: Dict[str, Any]) -> List:
        """Crea la sección de resumen de ventas"""
        elements = []
        
        elements.append(Paragraph("RESUMEN DE VENTAS", self.styles['CustomHeading']))
        
        # Tabla de resumen
        summary_data = [
            ['Total de Ventas:', f"${closure_data.get('total_sales', 0):,.2f}"],
            ['Productos Vendidos:', str(closure_data.get('total_products_sold', 0))],
            ['Membresías Vendidas:', str(closure_data.get('total_memberships_sold', 0))],
            ['Accesos Diarios:', str(closure_data.get('total_daily_access_sold', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightgrey),
        ]))
        
        elements.append(summary_table)
        return elements
    
    def _create_payment_breakdown_section(self, closure_data: Dict[str, Any]) -> List:
        """Crea la sección de desglose por método de pago"""
        elements = []
        
        elements.append(Paragraph("DESGLOSE POR MÉTODO DE PAGO", self.styles['CustomHeading']))
        
        # Tabla de métodos de pago
        payment_data = [
            ['Método de Pago', 'Ventas del Sistema', 'Conteo Físico', 'Diferencia'],
            ['Efectivo', f"${closure_data.get('cash_sales', 0):,.2f}", f"${closure_data.get('cash_counted', 0):,.2f}", f"${closure_data.get('cash_difference', 0):,.2f}"],
            ['Nequi', f"${closure_data.get('nequi_sales', 0):,.2f}", f"${closure_data.get('nequi_counted', 0):,.2f}", f"${closure_data.get('nequi_difference', 0):,.2f}"],
            ['Bancolombia', f"${closure_data.get('bancolombia_sales', 0):,.2f}", f"${closure_data.get('bancolombia_counted', 0):,.2f}", f"${closure_data.get('bancolombia_difference', 0):,.2f}"],
            ['Daviplata', f"${closure_data.get('daviplata_sales', 0):,.2f}", f"${closure_data.get('daviplata_counted', 0):,.2f}", f"${closure_data.get('daviplata_difference', 0):,.2f}"],
            ['Tarjeta', f"${closure_data.get('card_sales', 0):,.2f}", f"${closure_data.get('card_counted', 0):,.2f}", f"${closure_data.get('card_difference', 0):,.2f}"],
            ['Transferencia', f"${closure_data.get('transfer_sales', 0):,.2f}", f"${closure_data.get('transfer_counted', 0):,.2f}", f"${closure_data.get('transfer_difference', 0):,.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(payment_table)
        return elements
    
    def _create_physical_count_section(self, closure_data: Dict[str, Any]) -> List:
        """Crea la sección de conteo físico y diferencias"""
        elements = []
        
        elements.append(Paragraph("CONTEO FÍSICO Y DIFERENCIAS", self.styles['CustomHeading']))
        
        # Calcular totales
        total_counted = sum([
            closure_data.get('cash_counted', 0),
            closure_data.get('nequi_counted', 0),
            closure_data.get('bancolombia_counted', 0),
            closure_data.get('daviplata_counted', 0),
            closure_data.get('card_counted', 0),
            closure_data.get('transfer_counted', 0)
        ])
        
        total_differences = sum([
            closure_data.get('cash_difference', 0),
            closure_data.get('nequi_difference', 0),
            closure_data.get('bancolombia_difference', 0),
            closure_data.get('daviplata_difference', 0),
            closure_data.get('card_difference', 0),
            closure_data.get('transfer_difference', 0)
        ])
        
        # Tabla de totales
        totals_data = [
            ['Total Ventas del Sistema:', f"${closure_data.get('total_sales', 0):,.2f}"],
            ['Total Conteo Físico:', f"${total_counted:,.2f}"],
            ['Total Diferencias:', f"${total_differences:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[2.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightgrey),
        ]))
        
        elements.append(totals_table)
        return elements
    
    def _create_items_sold_section(self, items_data: Dict[str, Any]) -> List:
        """Crea la sección de items vendidos"""
        elements = []
        
        elements.append(Paragraph("ITEMS VENDIDOS EN EL TURNO", self.styles['CustomHeading']))
        
        # Resumen de items
        summary_data = [
            ['Productos Únicos:', str(items_data.get('total_products_sold', 0))],
            ['Items Totales:', str(items_data.get('total_items_sold', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightgrey),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 12))
        
        # Tabla de items vendidos
        if items_data.get('items_sold'):
            items_header = ['Producto', 'Cantidad Vendida', 'Stock Restante', 'Precio Unit.', 'Total']
            items_table_data = [items_header]
            
            for item in items_data['items_sold']:
                total_value = item['quantity_sold'] * item['unit_price']
                items_table_data.append([
                    item['product_name'],
                    str(item['quantity_sold']),
                    str(item['remaining_stock']),
                    f"${item['unit_price']:,.2f}",
                    f"${total_value:,.2f}"
                ])
            
            items_table = Table(items_table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(items_table)
        
        return elements
    
    def _create_notes_section(self, closure_data: Dict[str, Any]) -> List:
        """Crea la sección de notas"""
        elements = []
        
        elements.append(Paragraph("NOTAS", self.styles['CustomHeading']))
        elements.append(Paragraph(closure_data.get('notes', ''), self.styles['CustomNormal']))
        
        return elements
