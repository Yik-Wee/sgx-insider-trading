import json
import xml.etree.ElementTree as ET
from pdf_parser import extract_xml_from_xfa, xml_get_text
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from pypdf._reader import StrByteType
from enum import Enum
from pprint import pformat

_NAMESPACES = {"xfa": "http://www.xfa.org/schema/xfa-data/1.0/"}


class SecurityType(str, Enum):
    ORDINARY_SHARES = 1
    OTHER_SHARES = 2
    RIGHTS_OPTIONS_WARRANTS = 3
    DEBENTURES = 4
    RIGHTS_OPTIONS_OF_DEBENTURES = 5
    CONTRACTS = 6
    PARTICIPATORY_INTERESTS = 7
    OTHERS = 8


def money_str_to_float(text: str, default: Optional[float] = None) -> float | None:
    """
    Extracts numbers from a money string, e.g.
    ```
    # Valid
    money_str_to_float("16000.69") == 16000.69
    money_str_to_float("SGD16,000.69") == 16000.69
    money_str_to_float("S$16000.69") == 16000.69
    money_str_to_float("SGD$16.00069k") == 16000.69
    money_str_to_float("SGD$16.9m") == 16900000
    money_str_to_float("SGD$16.9b") == 16900000000
    money_str_to_float("SGD$16.9t") == 16900000000000
    money_str_to_float("SGD16e3") == 16000
    money_str_to_float("SGD16e2k") == 1600000

    # Invalid
    money_str_to_float("")
    money_str_to_float("16.9.0")
    money_str_to_float("SGD16ke3")
    money_str_to_float("SGD16x10^9")
    ```

    Returns
    ------
    the `float` amt of money, or `default` if invalid. If not specified, `defualt` is None

    Note
    ------
    Takes abbreviations up to "t" for trillion
    """
    text = text.lower().replace(",", "")
    output = ""
    idx_start = -1
    idx_end = -1

    for i in range(len(text)):
        if text[i].isdecimal():
            idx_start = i
            break

    for i in range(len(text)-1, -1, -1):
        if text[i].isdecimal():
            idx_end = i
            break

    if idx_start == -1 or idx_end == -1:
        return default

    if text.endswith("k"):
        factor = 1_000
    elif text.endswith("m") or text.endswith("mm"):
        factor = 1_000_000
    elif text.endswith("b"):
        factor = 1_000_000_000
    elif text.endswith("t"):
        factor = 1_000_000_000_000
    else:
        factor = 1

    try:
        print(f"{text} ->", text[idx_start:idx_end+1])
        output = float(text[idx_start:idx_end+1])
    except ValueError:
        return default

    return round(output * factor, 2)


# TODO Form types
# https://www.mas.gov.sg/regulation/capital-markets/disclosure-of-interest-in-listed-securities
class NotificationForm:
    """
    Base class for Securities and Futures Act notification forms
    """

    def __init__(self, stream: Union[StrByteType, Path]) -> None:
        self.__xml = extract_xml_from_xfa(stream)
        self._issuer_name = None
        self._issuer_type = None
        self._insider_name = None
        self._insider_title = None
        self._trade_date = None
        self._securities_before = None
        self._securities_after = None
        self._amt_consideration = None

    def _xml(self) -> ET.Element:
        return self.__xml

    def issuer_name(self) -> str:
        return self._issuer_name

    def issuer_type(self) -> str:
        return self._issuer_type

    def insider_name(self) -> str:
        return self._insider_name

    def insider_title(self) -> str:
        return self._insider_title

    def trade_date(self) -> str:
        return self._trade_date

    def securities_before(self) -> Dict[SecurityType, int]:
        pass

    def securities_after(self) -> Dict[SecurityType, int]:
        pass

    def amt_consideration(self) -> int:
        return self._amt_consideration

    def __str__(self) -> str:
        return f"""
TRADE DATE: {self.trade_date()}
ISSUER NAME: {self.issuer_name()}
ISSUER TYPE: {self.issuer_type()}
INSIDER TITLE: {self.insider_title()}
INSIDER NAME: {self.insider_name()}
AMT SECURITIES (BEF): {pformat(self.securities_before(), indent=2)}
AMT SECURITIES (AFT): {pformat(self.securities_after(), indent=2)}
AMT CONSIDERATION (PAID/RECV): {self.amt_consideration()}"""


class NotificationForm1(NotificationForm):
    """
    Purpose: Interests or changes in interests in the securities of listed issuer
    By:
    Director/CEO of:
    Listed corporation
    Trustee-manager of listed business trust (BT)
    Responsible person of listed real estate investment trust (REIT)

    To:
    Listed corporation
    Trustee-manager of listed BT
    Responsible person of listed REIT
    """

    def __init__(self, stream: StrByteType | Path) -> None:
        super().__init__(stream)
        self._insider_title = "Director/CEO"
        self._is_notifying_at_appt_time = xml_get_text(
            self._xml(), "Form1/Part1/notifyingAtApptTime"
        ).strip()

        (
            self._securities_before,
            self._securities_after,
        ) = self.__parse_part_3_securities()

    def is_notifying_at_appt_time(self) -> bool:
        """
        `True` if Director is notifying his interest at time of appointment (Part II),
        `False` if not (Part III)
        """
        return self._is_notifying_at_appt_time == "1"

    def issuer_name(self) -> str:
        if self._issuer_name is None:
            self._issuer_name = xml_get_text(
                self._xml(), "Form1/Part1/listedIssuer/name"
            )
        return self._issuer_name

    def issuer_type(self) -> str:
        if self._issuer_type is None:
            self._issuer_type = xml_get_text(
                self._xml(), "Form1/Part1/listedIssuer/type"
            )

        if self._issuer_type == "1":
            return "Company/Corporation"
        elif self._issuer_type == "2":
            return "Registered/Recognised Business Trust"
        elif self._issuer_type == "3":
            return "Real Estate Investment Trust"

        return self._issuer_type

    def insider_name(self) -> str:
        if self._insider_name is None:
            self._insider_name = xml_get_text(self._xml(), "Form1/Part1/nameDirector")
        return self._insider_name

    def trade_date(self) -> str:
        if self._trade_date is not None:
            return self._trade_date

        if self.is_notifying_at_appt_time():
            # Part II
            self._trade_date = xml_get_text(
                self._xml(), "Form1/Part2/dateAppointmentDirectorLI"
            )
        else:
            # Part III
            self._trade_date = xml_get_text(
                self._xml(), "Form1/Part3/Transaction/dateAquisition"
            )
        return self._trade_date

    def __parse_part_2_securities(self) -> Dict[SecurityType, int] | None:
        part_2_node = self._xml().find(".//xfa:data/SFA289/Form1/Part2/T1", _NAMESPACES)
        if part_2_node is None:
            return None

        tags = [
            (SecurityType.ORDINARY_SHARES, "ord/num/tot"),
            (SecurityType.OTHER_SHARES, "othx/tot"),
            (SecurityType.RIGHTS_OPTIONS_WARRANTS, "opt/num/tot"),
            (SecurityType.DEBENTURES, "deb/amt/tot"),
            (SecurityType.RIGHTS_OPTIONS_OF_DEBENTURES, "rDeb/amt/tot"),
            (SecurityType.CONTRACTS, "con/amt/tot"),
            (SecurityType.PARTICIPATORY_INTERESTS, "opt/part/tot"),
            (SecurityType.OTHERS, "opt/oth/tot"),
        ]

        securities_by_type = {}
        for tag in tags:
            text = xml_get_text(part_2_node, tag[1])
            if text:
                securities_by_type[tag[0]] = int(text.replace(",", ""))
        return securities_by_type

    def __parse_part_3_securities(
        self,
    ) -> Tuple[Dict[SecurityType, int], Dict[SecurityType, int]] | Tuple[None, None]:
        part_3_node = self._xml().find(
            ".//xfa:data/SFA289/Form1/Part3/Transaction", _NAMESPACES
        )
        if part_3_node is None:
            return (None, None)

        # Get type of securities present
        tags = [
            (SecurityType.ORDINARY_SHARES, "T1Ord", "num/tot"),
            (SecurityType.OTHER_SHARES, "T2Othx", "tot"),
            (SecurityType.RIGHTS_OPTIONS_WARRANTS, "T3Opt", "num/tot"),
            (SecurityType.DEBENTURES, "T4Deb", "amt/tot"),
            (SecurityType.RIGHTS_OPTIONS_OF_DEBENTURES, "T5RDeb", "amt/tot"),
            (SecurityType.CONTRACTS, "T6Con", "amt/tot"),
            (SecurityType.partition, "T7Part", "part/tot"),
            (SecurityType.OTHERS, "T8Oth", "oth/tot"),
        ]

        securities_before = {}
        securities_after = {}

        for tag in tags:
            text = xml_get_text(part_3_node, f"{tag[1]}/before/{tag[2]}")
            if text:
                securities_before[tag[0]] = int(text.replace(",", ""))

            text = xml_get_text(part_3_node, f"{tag[1]}/after/{tag[2]}")
            if text:
                securities_after[tag[0]] = int(text.replace(",", ""))

        self._part_3_securities = (securities_before, securities_after)
        return self._part_3_securities

    def securities_before(self) -> Dict[SecurityType, int]:
        if self._securities_before is not None:
            return self._securities_before

        if self.is_notifying_at_appt_time():
            # Get from Part II
            self._securities_before = self.__parse_part_2_securities()

        # Otherwise, get from Part III
        return self._securities_before

    def securities_after(self) -> Dict[SecurityType, int]:
        if self._securities_after is not None:
            return self._securities_after

        if self.is_notifying_at_appt_time():
            # Get from Part II -> same as securities before
            # when notifying at appt time, no change in total securities held, the filing
            # is just to inform of EXISTING securities held (i.e. before time of appt)
            return self.securities_before()

        # Otherwise, get from Part III
        return self._securities_after

    def amt_consideration(self) -> int:
        """
        Returns the amt of consideration in SGD obtained from transaction as a `str`.
        (Returned as `str` as the text is inconsistent)
        """
        if self._amt_consideration is None:
            if self.is_notifying_at_appt_time():
                # Part II
                self._amt_consideration = 0
                return 0

            self._amt_consideration = money_str_to_float(
                xml_get_text(self._xml(), "Form1/Part3/Transaction/amtConsideration"),
                default=0
            )

        return self._amt_consideration

    def __str__(self) -> str:
        return f"{super().__str__()}\nNOTIFYING AT TIME OF APPT: {self.is_notifying_at_appt_time()}"


class NotificationForm2(NotificationForm):
    """
    Purpose: Interests or changes in interests in the securities of a related corporation of the listed company
    By:
    Director of listed company incorporated in Singapore

    To:
    Listed company

    TODO No electronic form on MAS website, only non-electronic form
    https://www.mas.gov.sg/regulation/capital-markets/disclosure-of-interest-in-listed-securities
    """


class NotificationForm3(NotificationForm):
    """
    form 3 examples
    part ii: https://ir.lianbeng.com.sg/static-files/cc624db0-6792-4507-b5a9-f240cca8d542
    no part ii: https://links.sgx.com/FileOpen/_Notice%20to%20SGX%20-%20Form%203%20-%20Substantial%20Shareholder.ValueCap.11012016.draft2.ashx?App=ArchiveAnnouncement&FileID=385412&AnncID=C6BH3V3C5LGF4BN8

    Purpose: Changes in percentage level of interests in voting shares of listed corporation or voting units in listed BT/REIT
    By:
    Substantial shareholder of listed corporation
    Substantial unitholder of listed BT or REIT

    To:
    Listed corporation
    Trustee-manager of listed BT
    Responsible person and trustee of listed REIT
    """


# TODO are registered holders useful? They don't necessarily count as insiders, they just hold
# TODO their stocks directly with the company, instead of through a broker
class NotificationForm4(NotificationForm):
    """
    Purpose: Interests or changes in interests in the securities of listed issuer
    By:
    Registered holder of securities in listed issuer

    To:
    Person who has a deemed interest in the securities
    """


class NotificationForm5(NotificationForm):
    """
    TODO I don't understand what this means...
    TODO example:
    TODO - https://links.sgx.com/FileOpen/_Form%205_OUELH.ashx?App=Announcement&FileID=531359
    TODO - https://links.sgx.com/FileOpen/1.%20Announcement%20-%20Acquisition%20of%20Interest%20in%20Bowsprit%20Capital%20Corporation%20Limited.ashx?App=Announcement&FileID=525402

    Changes in interests in the voting shares of the trustee-manager or responsible person
    By:
    Shareholder of an unlisted trustee-manager of a listed BT
    Shareholder of an unlisted responsible person of a listed REIT

    To:
    Trustee-manager of listed BT
    Responsible person of listed REIT
    """


class NotificationForm6(NotificationForm):
    """
    example: https://links.sgx.com/FileOpen/_KRML.Form.6.FINAL.ashx?App=ArchiveAnnouncement&FileID=293302&AnncID=7MSPCMHRQG9TCYQM

    Puspose: Interests or changes in interests in the securities of the BT/REIT
    By:
    Trustee-manager of a listed BT
    Responsible person of a listed REIT

    To:
    Investors via SGXNet announcement (i.e. Form 7)
    """


class NotificationForm7(NotificationForm):
    """
    Forms 1, 3 and 5 received from directors, CEOs, substantial shareholders/unitholders
    and shareholders of unlisted trustee-manager/responsible person, and Form 6

    Note: This form is set out as an announcement template which can be accessed on SGXNet.

    By:
    Listed corporation
    Trustee-manager of listed BT
    Responsible person of listed REIT

    To:
    Investors
    TODO useful or not?
    """


# class NotificationFormC(NotificationForm):
#     """
#     NOT MADE PUBLIC
#     Particulars and contact information
#     By:
#     Reporting person giving notice using Form 1, 3, 5, 6
#     Listed issuer

#     To:
#     Listed issuer and the Authority
#     """
