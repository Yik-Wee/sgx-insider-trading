# https://stackoverflow.com/questions/68261052/pypdf-unable-to-read-xfa-pdf-file-after-it-has-been-filled-in-using-itextsharp
from pathlib import Path
from typing import Union
from pypdf import PdfReader
from pypdf._reader import StrByteType
import xml.etree.ElementTree as ET


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
    - if there is no `/Root`, `/AcroForm` or `/XFA` in the pdf
    - if the xml was unable to be decoded or parsed
    """

    reader = PdfReader(stream)

    try:
        root = reader.trailer["/Root"]
        acro_form = root["/AcroForm"]
        xfa = acro_form["/XFA"]
    except Exception as err:
        raise PdfParserException("Missing attribute in pdf") from err

    xml = None

    # find element after 'datasets', it is the xml object
    # pylint: disable=C0200
    for i in range(len(xfa)):
        if xfa[i] == "datasets":
            xml = xfa[i + 1].get_object().get_data()

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
    element = root.find(f".//{field}")
    if element is None:
        return ""

    if element.text is None:
        return ""
    return element.text


class XfaWriter:
    def __init__(self) -> None:
        pass

    def write(self, field: str, value: str, **kwargs) -> bool:
        """
        Write the `value` to the xml `field`, with `**kwargs` according to
        the `Element.find(..., **kwargs)` method
        """
        pass

    def __render(self) -> bool:
        """Render the XFA form into bytes"""
        pass

    def save_pdf(self, path: str) -> None:
        """Save the XFA Form to a pdf to the specified file `path`"""
        pass
