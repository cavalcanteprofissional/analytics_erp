# src/mermaid_renderer.py
import streamlit as st
import base64
from typing import Optional
import tempfile
import os

class MermaidRenderer:
    """Renderiza diagramas Mermaid no Streamlit"""
    
    @staticmethod
    def render(mermaid_code: str, height: int = 500) -> None:
        """Renderiza código Mermaid no Streamlit"""
        
        # CSS para estilizar
        mermaid_css = """
        <style>
        .mermaid-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #e0e0e0;
            overflow: auto;
        }
        </style>
        """
        
        # HTML com Mermaid
        mermaid_html = f"""
        <div class="mermaid-container">
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                er: {{
                    layoutDirection: 'LR',
                    minEntityWidth: 100,
                    minEntityHeight: 75,
                    entityPadding: 15
                }}
            }});
        </script>
        
        <div class="mermaid">
        {mermaid_code}
        </div>
        </div>
        
        <script>
        // Força redesenho se necessário
        setTimeout(() => {{
            if (typeof mermaid !== 'undefined') {{
                mermaid.contentLoaded();
            }}
        }}, 100);
        </script>
        """
        
        st.components.v1.html(mermaid_css + mermaid_html, height=height)
    
    @staticmethod
    def render_alternative(mermaid_code: str) -> None:
        """Alternativa usando streamlit.components"""
        import streamlit.components.v1 as components
        
        # Componente customizado
        components.html(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default',
                        er: {{
                            layoutDirection: 'LR'
                        }}
                    }});
                </script>
                <style>
                    body {{
                        margin: 0;
                        padding: 10px;
                    }}
                    .mermaid {{
                        width: 100%;
                        height: auto;
                    }}
                </style>
            </head>
            <body>
                <div class="mermaid">
                {mermaid_code}
                </div>
            </body>
            </html>
            """,
            height=600,
            scrolling=True
        )
    
    @staticmethod
    def create_download_button(mermaid_code: str, filename: str = "er_diagram.mmd"):
        """Cria botão para download do diagrama"""
        
        # Codifica para base64
        b64 = base64.b64encode(mermaid_code.encode()).decode()
        
        # HTML para download
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">📥 Download Diagrama Mermaid</a>'
        st.markdown(href, unsafe_allow_html=True)