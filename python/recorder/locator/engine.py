class LocatorEngine:
    def __init__(self):
        pass

    def generate_locators(self, element_data: dict) -> list:
        """
        Takes raw DOM element data and generates a list of possible locators
        ranked by confidence.
        """
        locators = []
        
        if element_data.get("id"):
            locators.append({"type": "id", "value": f"id={element_data['id']}", "confidence": 0.98})
            
        if element_data.get("name"):
            locators.append({"type": "name", "value": f"name={element_data['name']}", "confidence": 0.95})
            
        if element_data.get("css"):
            locators.append({"type": "css", "value": f"css={element_data['css']}", "confidence": 0.90})
            
        if element_data.get("xpath"):
            locators.append({"type": "xpath", "value": f"xpath={element_data['xpath']}", "confidence": 0.85})
            
        # Sort by confidence descending
        locators.sort(key=lambda x: x["confidence"], reverse=True)
        return locators
