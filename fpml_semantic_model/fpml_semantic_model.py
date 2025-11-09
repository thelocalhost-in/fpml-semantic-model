import json
import sys
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# 1. FPML STRUCTURAL MODEL (Structural Analysis and XML Generation)
# ----------------------------------------------------------------------

DEFAULT_FPML_XSD_JSON_DATA = "all_xsd_data.json"
DEFAULT_EMBEDDINGS_JSON_DATA = "generated_embeddings.json"

class FpMLBaseModel:
    """
    Analyzes FpML XSD structure, provides structured data access, and 
    generates minimal XML message snippets.
    """
    def __init__(self, file_path: str=None):
        if file_path is None:
            self.file_path = DEFAULT_FPML_XSD_JSON_DATA
        else:
            self.file_path = file_path
        self.data: Dict[str, Any] = self._build_model()

    def _build_model(self) -> Dict[str, Any]:
        """Loads and processes XSD data into the comprehensive lookup dictionary."""
        try:
            with open(self.file_path, 'r') as f:
                xsd_data = json.load(f)
        except Exception as e:
            print(f"Error loading or processing file: {e}", file=sys.stderr)
            return {}

        model = {}
        
        for xsd_file, content in xsd_data.items():
            
            # Helper to process both top-level elements and complex type children
            def process_element_list(elements: List[Dict], location_type: str, type_doc: str = ''):
                for element in elements:
                    tag_name = element.get('name')
                    if tag_name and tag_name not in model:
                        model[tag_name] = self._extract_details(element, xsd_file, location_type, type_doc)

            # A. Process Top-Level Elements
            process_element_list(content.get('elements', []), 'Top-Level Element')

            # B. Process Complex Types (for nested fields)
            for type_def in content.get('complexTypes', []):
                type_name = type_def.get('name')
                type_doc = type_def.get('documentation', 'No description available for complex type.')
                process_element_list(type_def.get('children', []), f'Child of {type_name}', type_doc)

        print(f"✅ FpML Structural Model built. Total unique tags indexed: {len(model)}")
        return model

    def _extract_details(self, element: Dict, xsd_file: str, location: str, type_doc: str = '') -> Dict:
        """Helper to extract consistent details from an element dictionary."""
        return {
            'source_xsd': xsd_file,
            'data_type': element.get('type', 'N/A'),
            'description': element.get('documentation', type_doc or 'No description available'),
            'attributes': element.get('attributes', {}),
            'children': element.get('children', []),
            'minOccurs': element.get('minOccurs', '1'), # Include minOccurs for XML generation
            'maxOccurs': element.get('maxOccurs', '1'), # Include maxOccurs for XML generation
            'location_type': location
        }

    def lookup_tag(self, tag_name: str) -> Dict[str, Any]:
        """Retrieves structured details for a given FpML tag name (Exact Match)."""
        details = self.data.get(tag_name)
        if details:
            return {
                'Tag Name': tag_name,
                'Source XSD': details.get('source_xsd'),
                'Data Type': details.get('data_type'),
                'Location': details.get('location_type'),
                'Description': details.get('description', 'N/A'),
                'Attributes': details.get('attributes', {}),
                'Children Count': len(details.get('children', [])),
                'Children Sample (First 2)': details.get('children', [])[:2]
            }
        return {"status": f"Tag '{tag_name}' not found in the Base Model."}

    # --- XML Generation Methods ---

    def _generate_xml_snippet(self, tag_name: str, indent: int) -> str:
        """
        Recursively generates a minimal XML snippet for a given tag and its required children.
        Only includes elements where minOccurs >= 1.
        """
        details = self.data.get(tag_name)
        if not details:
            return ""

        padding = "    " * indent
        
        # 1. Check if this element is a simple type (no complex children)
        children = details.get('children', [])
        is_complex = bool(children)
        
        # 2. Generate content recursively for required children
        inner_content = ""
        if is_complex:
            for child in children:
                child_name = child.get('name')
                min_occurs = child.get('minOccurs', '0')
                
                # Only include elements that are required (minOccurs >= 1) for a minimal message
                if int(min_occurs) >= 1:
                    inner_content += self._generate_xml_snippet(child_name, indent + 1)

        # 3. Determine the content/placeholder for the current tag
        if inner_content:
            # If complex and has required children, the content is the recursive output
            content = '\n' + inner_content + padding
            return f"{padding}<{tag_name}>{content}</{tag_name}>\n"
        
        else:
            # If complex but no required children, or if a simple type, use a placeholder
            data_type = details.get('data_type', 'xs:string')
            if 'Enum' in data_type:
                placeholder = f"ENUM_VALUE_FROM_{data_type}"
            else:
                placeholder = f"'{data_type}_VALUE'"
            
            return f"{padding}<{tag_name}>{placeholder}</{tag_name}>\n"


    def generate_xml_message(self, root_tag: str, namespace: str = "http://www.fpml.org/FpML-5/confirmation") -> Dict[str, str]:
        """
        Generates a minimal, valid XML message snippet for the given root FpML tag.
        
        Args:
            root_tag (str): The top-level FpML tag name (e.g., 'requestTradeConfirm').
            namespace (str): The FpML namespace to use (default for FpML-5).
            
        Returns:
            Dict[str, str]: Dictionary containing the generated XML and status.
        """
        details = self.data.get(root_tag)
        if not details or details.get('location_type') != 'Top-Level Element':
            return {"status": f"Root tag '{root_tag}' not found or is not a top-level message element."}

        # Recursively generate content, starting at indent 1
        content = self._generate_xml_snippet(root_tag, 1).strip()
        
        # Add XML declaration and namespace
        full_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<{root_tag} xmlns="{namespace}">
{content}
</{root_tag}>
"""
        return {"xml_snippet": full_xml}


# ----------------------------------------------------------------------
# 2. EXECUTION AND DEMONSTRATION (Structural Only)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    
    # The file "all_xsd_data.json" is required to run the model
    FPML_FILE_PATH = "all_xsd_data.json"
    
    # 1. Initialize the FpML Base Model
    fpml_base_model = FpMLBaseModel(file_path=FPML_FILE_PATH)
    
    # --- Demo Queries ---
    tags_to_lookup = [
        "bond",
        "requestConfirmation", # A specific loan tag from one of the XSD files
        "nonExistentTag"
    ]

    print("\n" + "="*80)
    print("FpML STRUCTURAL LOOKUP DEMONSTRATION")
    print("="*80)

    for tag in tags_to_lookup:
        
        # Perform Structural Lookup
        tag_details = fpml_base_model.lookup_tag(tag)
        
        # Display Results
        print("\n" + "-"*80)
        print(f"LOOKUP: {tag}")
        print("-"*80)
        
        if 'status' in tag_details:
            print(tag_details['status'])
        else:
            for key, value in tag_details.items():
                print(f"  {key}: {value}")