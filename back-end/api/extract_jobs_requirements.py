import re
from typing import List
import aiohttp
from bs4 import BeautifulSoup

async def extract_jobs_requirements(urls: List[str]) -> list:
    """
    Extract job requirements from multiple job posting URLs.
    
    Args:
        urls (List[str]): A list of URLs of job postings.
        
    Returns:
        list: A combined list of job requirements extracted from all job postings.
    """
    all_requirements = []
    
    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        all_requirements.append(f"Error for {url}: Unable to access the URL. Status code: {response.status}")
                        continue
                    
                    html_content = await response.text()
            
            soup = BeautifulSoup(html_content, "lxml")
            
            requirement_keywords = [
                "requirements", "qualifications", "what you need", 
                "skills required", "must have", "required skills",
                "job requirements", "minimum requirements", "advantages", 
                "nice to have"
            ]
            
            url_requirements = []
            
            # Method 1: Look for sections with requirements in the title
            requirement_sections = []
            for keyword in requirement_keywords:
                headers = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"], 
                                      string=re.compile(keyword, re.I))
                for header in headers:
                    parent = header.parent
                    next_element = header.find_next(["ul", "ol", "div", "p"])
                    
                    requirement_sections.extend([parent, next_element])
            
            # Method 2: Look for unordered or ordered lists that might contain requirements
            lists = soup.find_all(["ul", "ol"])
            for list_item in lists:
                prev_element = list_item.find_previous(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "p"])
                if prev_element and any(keyword in prev_element.get_text().lower() for keyword in requirement_keywords):
                    requirement_sections.append(list_item)
            
            for section in requirement_sections:
                if section:
                    if section.name in ["ul", "ol"]:
                        list_items = section.find_all("li")
                        for item in list_items:
                            text = item.get_text().strip()
                            if text and text not in url_requirements:
                                url_requirements.append(text)
                    else:
                        paragraphs = section.find_all(["p", "div", "span"])
                        for p in paragraphs:
                            text = p.get_text().strip()
                            if text and not any(req in text for req in url_requirements):
                                if len(text) > 20 and "." in text:
                                    sentences = [s.strip() for s in text.split(".") if s.strip()]
                                    for sentence in sentences:
                                        if sentence and sentence not in url_requirements:
                                            url_requirements.append(sentence)
                                else:
                                    url_requirements.append(text)
            
            # If no requirements found, try a more general approach
            if not url_requirements:
                bullet_points = soup.find_all("li")
                for point in bullet_points:
                    text = point.get_text().strip()
                    if text and len(text) > 10 and text not in url_requirements:
                        url_requirements.append(text)
            
            url_requirements = [re.sub(r"\s+", " ", req).strip() for req in url_requirements]
            url_requirements = [req for req in url_requirements if len(req) > 5]
            
            all_requirements.extend(url_requirements)
            
        except Exception as e:
            all_requirements.append(f"Error for {url}: {str(e)}")
    
    seen = set()
    all_requirements = [req for req in all_requirements if not (req in seen or seen.add(req))]
    
    return all_requirements if all_requirements else ["No specific requirements found on any of the pages"]

