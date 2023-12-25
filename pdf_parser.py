# https://stackoverflow.com/questions/68261052/pypdf-unable-to-read-xfa-pdf-file-after-it-has-been-filled-in-using-itextsharp
from pathlib import Path
from typing import Union
import xml.etree.ElementTree as ET
from pypdf import PdfReader
from pypdf._reader import StrByteType


class PdfParserException(Exception):
    pass


def extract_xml_from_xfa(
    stream: Union[StrByteType, Path],
    debug_filename=None,
) -> ET.Element | None:
    """
    Params
    ------
    stream: `StrByteType | Path`
    - A File object or an object that supports the standard read and seek methods similar
      to a File object. Could also be a string representing a path to a PDF file.

    Returns
    ------
    - The `xml.etree.ElementTree.Element` root of the xml document
    - `None` if no xml found

    Exceptions
    ------
    Raises `PdfParserException`
    - if an XFA was unable to be extracted
    - if the XML was unable to be decoded to UTF-8 or parsed
    """

    reader = PdfReader(stream)
    if reader.xfa is None:
        raise PdfParserException("No XFA in PDF")

    xml = reader.xfa.get("datasets")
    if xml is None:
        return None

    try:
        xml_string = xml.decode("utf-8")

        if debug_filename:
            with open(debug_filename, "w", encoding="UTF-8") as f:
                f.write(xml_string)

        xml_tree_root = ET.fromstring(xml_string)
        return xml_tree_root
    except Exception as err:
        raise PdfParserException("Unable to parse xml") from err


def xml_get_text(root: ET.Element, field: str) -> str:
    """
    Params
    ------
    root: `ET.Element`
    - The xml root

    field: `str`
    - The field to extract text from

    Returns
    ------
    the element's text, or empty str `""` if element not found or element has no text
    """
    element = root.find(f".//{field}")
    if element is None:
        return ""

    if element.text is None:
        return ""
    return element.text
