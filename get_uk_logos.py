import requests
import json
import os

def get_github_directory_content(repo_owner, repo_name, directory_path):
    """Get contents of a GitHub repository directory"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{directory_path}"
    response = requests.get(url)
    return response.json()

def save_filenames_to_txt(content_list, output_file):
    """Save filenames from GitHub API response to a text file"""
    with open(output_file, 'w') as f:
        for item in content_list:
            if item['type'] == 'file' and item['name'].endswith('.png'):
                name = item['name']
                download_url = item['download_url']
                f.write(f"{name}|{download_url}\n")

# Directory to save filenames
output_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(output_dir, "uk_tv_logos.txt")

# Get UK TV logos from GitHub
content = get_github_directory_content('tv-logo', 'tv-logos', 'countries/united-kingdom')
save_filenames_to_txt(content, output_file)

print(f"Filenames saved to {output_file}")
