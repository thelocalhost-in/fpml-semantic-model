import json
import sys
from typing import Dict, Any, List

class FpMLBaseModel:
    """
    A publishable class for analyzing FpML XSD structure and generating 
    template FpML XML messages.
    """
    def __init__(self, file_path: str):
        """Initializes the model by loading and processing the consolidated XSD JSON data."""
        self.file_path = file_path
        self.data: Dict[str, Any] = self._build_model()
        
        # Define standard FpML XML boilerplate
        self.fpml_ns = 'http://www.fpml.org/FpML-5/confirmation'
        self.xsd_prefix = '{http://www.w3.org/2001/XMLSchema}'

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
            
            # A. Process Top-Level Elements
            for element in content.get('elements', []):
                tag_name = element.get('name')
                if not tag_name or tag_name in model:
                    continue
                model[tag_name] = self._extract_details(element, xsd_file, 'Top-Level Element')

            # B. Process Complex Types (for nested fields)
            for type_def in content.get('complexTypes', []):
                type_name = type_def.get('name')
                type_doc = type_def.get('documentation', 'No description available for complex type.')
                
                for child in type_def.get('children', []):
                    child_name = child.get('name')
                    if child_name and child_name not in model:
                        model[child_name] = self._extract_details(
                            child, xsd_file, f'Child of {type_name}', type_doc=type_doc
                        )

        print(f"✅ Model built successfully. Total unique tags indexed: {len(model)}")
        return model

    def _extract_details(self, element: Dict, xsd_file: str, location: str, type_doc: str = '') -> Dict:
        """Helper to extract consistent details from an element dictionary."""
        return {
            'source_xsd': xsd_file,
            'data_type': element.get('type', 'N/A'),
            'description': element.get('documentation', type_doc or 'No description available'),
            'attributes': element.get('attributes', {}),
            'children': element.get('children', []),
            'location_type': location
        }

    def lookup_tag(self, tag_name: str) -> Dict[str, Any]:
        """Retrieves structured details for a given FpML tag name."""
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
        return {"status": f"Tag '{tag_name}' not found in the FpML Base Model."}

    def _build_xml_recursively(self, tag_name: str, depth: int, max_depth: int) -> str:
        """Recursively builds a template XML fragment."""
        if depth > max_depth:
            return ""

        details = self.data.get(tag_name)
        if not details:
            return ""

        indent = "  " * depth
        
        # 1. Start Tag and Attributes
        attr_str = ""
        for attr_name, attr_details in details.get('attributes', {}).items():
            # Add a mock value for required attributes
            if attr_details.get('use') == 'required':
                attr_str += f' {attr_name}="VALUE_REQUIRED"'
        
        xml_fragment = f"{indent}<{tag_name}{attr_str}>"
        
        # 2. Add Content or Children
        if details.get('data_type') not in ['N/A', None] and not details.get('children'):
            # If it's a simple type (leaf node), add a placeholder value
            xml_fragment += f"PLACEHOLDER_{details.get('data_type')}"
        elif details.get('children'):
            xml_fragment += "\n"
            # Recursively add children
            for child in details['children']:
                # Use minOccurs/maxOccurs to decide which children to include, here we include all defined children
                child_name = child.get('name')
                xml_fragment += self._build_xml_recursively(child_name, depth + 1, max_depth)
            
            # Close the tag only after children
            xml_fragment += f"{indent}</{tag_name}>"
        else:
            # Handle empty tags or complex types with no children listed
            xml_fragment += f"</{tag_name}>"


        # Handle self-closing tags if no content or children are generated
        if "PLACEHOLDER" in xml_fragment or xml_fragment.strip().endswith(f"</{tag_name}>"):
            return xml_fragment.strip() if "\n" not in xml_fragment else xml_fragment

        # Default close for non-leaf nodes
        return f"{xml_fragment}\n{indent}</{tag_name}>"
    

    def generate_message(self, root_tag: str, max_depth: int = 3) -> str:
        """
        Generates a template FpML XML message starting with the specified root_tag.
        
        Parameters:
            root_tag (str): The top-level FpML element (e.g., 'bond', 'requestEventStatus').
            max_depth (int): The maximum depth to traverse the structure for simplicity.
        """
        if root_tag not in self.data:
            return f"Error: Root tag '{root_tag}' not found in the Base Model."

        # Start the XML document with FpML wrapper
        xml_output = [
            '<?xml version="1.0" encoding="utf-8"?>',
            f'<{'fpml'}:{'dataDocument'} xmlns:{'fpml'}="{self.fpml_ns}" version="5-12">'
        ]
        
        # 1. Build the root structure recursively
        content = self._build_xml_recursively(root_tag, 1, max_depth)
        xml_output.append(content)

        # 2. Close the FpML wrapper
        xml_output.append(f'</{'fpml'}:{'dataDocument'}>')

        return "\n".join(xml_output)

# ----------------------------------------------------------------------
# DEMONSTRATION
# ----------------------------------------------------------------------

# Initialize the published model
fpml_model = FpMLBaseModel(file_path="all_xsd_data.json")

# --- Step 1: Look up the tag structure ---
print("\n" + "="*70)
print("Demo 1: Structural Lookup for 'requestConfirmation'")
print("="*70)
bond_structure = fpml_model.lookup_tag('requestConfirmation')
print(json.dumps(bond_structure, indent=4))

# --- Step 2: Generate FpML Message Template (using 'bond' as the message type) ---
print("\n" + "="*70)
print("Demo 2: FpML Message Generation for 'requestConfirmation'")
print("="*70)
bond_message_template = fpml_model.generate_message(root_tag='requestConfirmation', max_depth=3)
print(bond_message_template)