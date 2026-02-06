"""
Templates HTML para correos de bienvenida
"""

def get_email_template(empresa, nombre, imagen_url):
    """
    Retorna el template HTML según la empresa
    """
    
    # Configuración de imágenes
    IMAGENES = {
        'bienvenida': imagen_url,
    }
    
    # Textos según empresa
    TEXTOS = {
        'cramer': {
            'saludo': f'Buenos días {nombre}.',
            'bienvenida': '¡Te damos la bienvenida a Cramer!',
            'descripcion': 'A continuación te entregamos una guía para ayudarte a resolver dudas en tus primeros días en nuestra empresa. Haz Click para revisarla cada vez que lo estimes necesario.'
        },
        'syf': {
            'saludo': f'Buenos días {nombre}.',
            'bienvenida': '¡Te damos la bienvenida a Sabores y Fragancias!',
            'descripcion': 'A continuación te entregamos una guía para ayudarte a resolver dudas en tus primeros días en nuestra empresa. Haz Click para revisarla cada vez que lo estimes necesario.'
        }
    }
    
    texto = TEXTOS.get(empresa, TEXTOS['cramer'])
    
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>¡Bienvenido a Cramer!</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                    
                    <tr>
                        <td style="padding: 30px 20px;">
                            <p style="margin: 0; font-size: 16px; color: #333333; line-height: 1.6;">
                                {texto['bienvenida']}<br><br>
                                {texto['saludo']}<br><br>
                                En la siguiente página te entregamos una guía que te ayudará a resolver dudas en tus primeros días en nuestra empresa. Puedes revisarla cada vez que lo estimes necesario.
                            </p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 20px 20px 20px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f9f9f9; border-radius: 6px; overflow: hidden;">
                                <tr>
                                    <td width="192" valign="top" style="padding: 15px;">
                                        <a href="https://carloscramerproductos.sharepoint.com/sites/chile/SitePages/%C2%BFQu%C3%A9-debo-saber-.aspx" target="_blank" style="text-decoration: none;">
                                            <img src="{IMAGENES['bienvenida']}" alt="¡TE DAMOS LA BIENVENIDA!" width="192" height="108" style="display: block; border: none; border-radius: 4px;">
                                        </a>
                                    </td>
                                    
                                    <td valign="top" style="padding: 15px;">
                                        <a href="https://carloscramerproductos.sharepoint.com/sites/chile/SitePages/%C2%BFQu%C3%A9-debo-saber-.aspx" target="_blank" style="text-decoration: none;">
                                            <h3 style="margin: 0 0 10px 0; font-size: 18px; color: #0078D7; font-weight: 600;">
                                                ¡TE DAMOS LA BIENVENIDA!
                                            </h3>
                                        </a>
                                        
                                        <p style="margin: 0; font-size: 13px; color: #666666; line-height: 1.5;">
                                            {texto['descripcion']}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
