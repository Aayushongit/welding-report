
import os
import glob

def get_files(weld_type):
    """Get video and image files for a given welding type."""
    # Paths for file existence checks, relative to the project root
    check_base_path = f'./{weld_type}'
    
    # Paths for the HTML src attributes, relative to the website/index.html file
    html_base_path = f'../{weld_type}'

    if weld_type == 'ERW':
        # Special handling for ERW, as its output is in the root output directory
        check_base_path = './'
        html_base_path = '../'
        
        video_check_path = './ERW/erw_simulation.mp4'
        video_html_path = '../ERW/erw_simulation.mp4'
        videos = [video_html_path] if os.path.exists(video_check_path) else []

        found_images = glob.glob(os.path.join(check_base_path, 'output', '*.png'))
        images = [os.path.join(html_base_path, 'output', os.path.basename(img)) for img in found_images]
        return videos, images

    if weld_type == 'tig-ele':
        check_base_path = './tig-ele'
        html_base_path = '../tig-ele'
        sub_folders = ['output_electrode_gas', 'output_electrode_no_gas', 'output_tig_gas', 'output_tig_no_gas']
        
        video_check_path = './tig-ele/tig_simulation.mp4'
        video_html_path = '../tig-ele/tig_simulation.mp4'
        videos = [video_html_path] if os.path.exists(video_check_path) else []

        images = []
        for folder in sub_folders:
            # Find files using the check path
            found_files = glob.glob(os.path.join(check_base_path, folder, '*.png'))
            # Add the html path for each found file
            images.extend([os.path.join(html_base_path, folder, os.path.basename(f)) for f in found_files])
        return videos, images

    video_check_path = os.path.join(check_base_path, f'{weld_type.lower()}_simulation.mp4')
    video_html_path = os.path.join(html_base_path, f'{weld_type.lower()}_simulation.mp4')

    if not os.path.exists(video_check_path):
        video_check_path = os.path.join(check_base_path, 'output', 'vedio.mp4') # fallback for ebw
        video_html_path = os.path.join(html_base_path, 'output', 'vedio.mp4')

    if not os.path.exists(video_check_path):
        video_check_path = os.path.join(check_base_path, 'output', 'welding_simulation.mp4') # fallback for lbw
        video_html_path = os.path.join(html_base_path, 'output', 'welding_simulation.mp4')

    videos = [video_html_path] if os.path.exists(video_check_path) else []
    
    # Find images using the check path
    found_images = glob.glob(os.path.join(check_base_path, 'output', '*.png'))
    # Create the list of image paths for the HTML
    images = [os.path.join(html_base_path, 'output', os.path.basename(img)) for img in found_images]
    
    return videos, images

def create_website():
    """Generate the HTML for the website."""
    weld_types = ['ebw', 'ERW', 'lbw', 'paw', 'saw', 'tig-ele']
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welding Simulations</title>
    <style>
        body {
            background-color: #333;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2 {
            text-align: center;
            color: #fff;
        }
        .weld-section {
            background-color: #444;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .media-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }
        video, img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        .video-container, .image-container {
            flex: 1 1 45%;
            min-width: 300px;
        }
        .explanation {
            margin-top: 20px;
            padding: 15px;
            background-color: #555;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welding Simulation Showcase</h1>
"""

    for weld_type in weld_types:
        videos, images = get_files(weld_type)
        
        html_content += f"""
        <div class="weld-section">
            <h2>{weld_type.upper()} Welding</h2>
            <div class="media-container">
        """

        for video in videos:
            html_content += f"""
                <div class="video-container">
                    <h3>Simulation Video</h3>
                    <video controls>
                        <source src="{video}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
            """

        if images:
            html_content += """
                <div class="image-container">
                    <h3>Graphs and Plots</h3>
            """
            for image in sorted(images):
                html_content += f'<img src="{image}" alt="Graph for {weld_type}">'
            html_content += "</div>"

        html_content += """
            </div>
            <div class="explanation">
                <h3>Explanation</h3>
                <p><i>[Space for LaTeX or Markdown explanation of the {weld_type.upper()} simulation.]</i></p>
            </div>
        </div>
        """

    html_content += """
    </div>
</body>
</html>
"""
    with open('index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    create_website()
    print("Website generated successfully as index.html")

