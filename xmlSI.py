#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python 2.7

# Fredrik Forsberg 171107

# "##//" = Behöver ändras


import os, xml.etree.ElementTree

#

class xmlSI(xml.etree.ElementTree.ElementTree):

    """
    Klass för hantering av SI-data och import/export till xml-format.
    Ärver från xml.etree.ElementTree.ElementTree .

    self.addPunch() är den funktion som används för att lägga till
       stämpling och spara till fil. De andra är hjälpfunktioner.
    """ ##// Utöka beskrivning med exempel
    
    def __init__(self, filePath, competitionName=None, prettyPrint=True):

        """
        filePath: "str"
          Sökvägen för xml-filen. Skapar ny fil om den inte redan existerar.

        competitionName: "None" / "unicode"
          Tävlingens namn.
          Om "None" hämtas namnet från xml-filen alt. sätts till tom sträng om fil saknas.
          Textsträngen måste vara i unicode-format (u"") vid hantering av icke-ascii.
          Om strängen inte matchar xml-filens sträng genereras ett felmeddelande.
        
        prettyPrint: "bool"
          Anger om indenteringar ska göras för läsbarhet istället för att allt är på
          samma rad.
        """

        # Sparar filsökvägen och tävlingsnamnet
        self.filePath = filePath
        self.competitionName = competitionName
        self.prettyPrint = bool(prettyPrint)

        # competitionName måste vara unicode (u""), annars blir det problem med icke-ascii
        # ( Ett DecodeError (ordinal not in range(128)) fås av 
        #    competitionName.encode('utf-8', errors="xmlcharrefreplace")
        #    i self.write() med icke-ascii och UTF-8. )
        try:
            if self.competitionName is not None:
                self.competitionName = unicode(self.competitionName)
        except UnicodeDecodeError as exc:
            raise UnicodeDecodeError(str(exc) + '\r\ncompetitionName must be unicode for xmlSI')

        
        if os.path.isfile(self.filePath):
            # xml-fil finns

            # Läser in xml-filen
            self._load()
            
        else:
            # xml-fil saknas
            
            # Om tävlingsnamn saknas sätt till tom sträng
            if self.competitionName is None:
                self.competitionName = u""

            # Initierar xml-trädet (self)
            xml.etree.ElementTree.ElementTree.__init__(self)
            
            # Initierar en rot för trädet
            self._setroot(xml.etree.ElementTree.Element(
                                    "competition",
                                    attrib={"name": self.competitionName}))

            # Skapa fil genom att spara
            self._save()


    #

    def _save(self):
        """
        Sparar trädet som xml-fil
        """
        
        # Indenterar om self.prettyPrint == True
        if self.prettyPrint:
            self._indent(self.getroot())

        self.write(self.filePath, encoding="utf-8")

    #

    def _load(self):
        """
        Läser in xml-fil och kontrollerar tävlingsnamn
        """
        # Läser xml-filen och initierar xml-trädet (self)
        xml.etree.ElementTree.ElementTree.parse(self, self.filePath)

        # Kontrollerar tävlingens namn
        if self.getroot().tag != "competition":
            raise ValueError('Error in xmlSI._load(): Wrong XML root tag: "' + self.getroot().tag + '". Expected: "competition".\r\nXML-file: ' + self.filePath)

        if "name" not in self.getroot().attrib:
            raise ValueError('Error in xmlSI._load(): XML root does not have the attribute "name".\r\nXML-file: ' + self.filePath)

        if self.competitionName is None:
            # Använd xml-filens tävlingsnamn
            self.competitionName = unicode(self.getroot().attrib["name"])
            
        elif ( isinstance(self.competitionName, unicode )
               and unicode(self.getroot().attrib["name"]) != self.competitionName ):
            
            raise ValueError('Error in xmlSI._load(): Inconsistent competition name. Input: "' + self.competitionName + '". XML: "' + unicode(self.getroot().attrib["name"]) + '".\r\nXML-file: ' + self.filePath)

    #
    
    def _add(self, elemDict, parent=None):
        """
        Lägger itterativt till element med taggar och eventuella värden och attribut
        baserat på "dict" elemDict:s uppbyggnad.

        elemDict = {'tag': '<tag>', 'attribute': {<attribute>}, 'text': <text>, 'subelement': {<subelement>}}

        <tag> är taggen för posten
        {<attribute>}:s poster visas som del av posten, efter 'tag'
        <text> är informationen mellan startflaggan och första subelementet alt. slutflaggan
        {<subelement>} är en "dict" med samma uppbyggnad som elemDict, alt. flera {<subelement>} i en "list"

        Exempel:
        <tag attribute="attribute">
          <subelementtag>text</subelementtag>
        </tag>

        Se funktionen "self.addPunch()" för användningsexempel.
        """

        # Argumentet "parent" är endast "None" första ittertionen => root
        # (Funktionen "self.getroot()" och övriga arvsfuntioner initieras först i __init__ och kan därför inte användas direkt som argument)
        if parent is None:
            parent = self.getroot()

            # Om elemDict är "list", kör _add på varje element
            if isinstance(elemDict, list):
                for item in elemDict:
                    self._add(item, parent)
                return

        # Tag från elemDict
        if 'tag' in elemDict:
            tag = elemDict['tag']
        else:
            raise ValueError('Error in xmlSI._add(): Missing a "tag" entry in the elemDict dictionary: ' + str(elemDict))

        # Attribut från elemDict
        attribute = {}
        if 'attribute' in elemDict:
            attribute = elemDict['attribute']

        # Text från elemDict
        text = None
        if 'text' in elemDict:
            text = elemDict['text']
        
        # Kontrollerar om elementet redan existerar till föräldern "parent"
        attributeString = ''
        for key in attribute:
            attributeString += "[@" + key + "='" + str(attribute[key]) + "']"
        
        element = parent.find("./" + tag + attributeString)

        # Kontrollerar så att <text> är samma (om den angetts)
        # Skapar annars en ny post
        if ( text is not None
             and element is not None
             and element.text != text ):
            
            element = None

            
        if element is None:
            # Elementet finns inte ännu. Lägger till elementet som ett subelement till föräldern "parent".
            element = xml.etree.ElementTree.SubElement(parent, tag, attrib=attribute)

        # Lägger itterativt till subelement
        if ( 'subelement' in elemDict
             and isinstance(elemDict['subelement'], dict)
             and len(elemDict['subelement']) > 0 ):
            
            # Om "dict" => Ett subelement
            self._add(elemDict['subelement'], element)

        elif ( 'subelement' in elemDict
             and isinstance(elemDict['subelement'], list)
             and len(elemDict['subelement']) > 0 ):

            # Om "list" => Flera subelement (varsitt "dict" i listan)
            for item in elemDict['subelement']:
                
                if ( isinstance(item, dict)
                     and len(item) > 0 ):

                    self._add(item, element)

        # Lägg till <text> för elementet
        if text is not None:
            element.text = text
    
    #
    
    def addPunch(self, SIstation, SIcard, Time, otherInfo=[{}]):
        """
        Lägger till element till xml-trädet.
        Används som mall för funktionen ._add() med specifika inputalternativ.
        Argumenten måste vara "str".


        self.addPunch('97', '920407', '2017-11-10 17:23:13') genererar följande:
        
        <competition name="Testlöpning">
          <SIstation Nr="97">
            <SIcard Nr="920407">
              <Punch Time="2017-11-10 17:23:13" />
            </SIcard>
          </SIstation>
        </competition>
        """

        # Konstruerar ett "dict" för "self._add()" från yttersta posten för tydlighetens skull
        PunchDict = {'tag': 'Punch', 'attribute': {'Time': unicode(Time)}, 'subelement': otherInfo}

        SIcardDict = {'tag': 'SIcard', 'attribute': {'Nr': unicode(SIcard)}, 'subelement': PunchDict}

        SIstationDict = {'tag': 'SIstation', 'attribute': {'Nr': unicode(SIstation)}, 'subelement': SIcardDict}

        # Använder "self._add()" för att lägga till stämplingen
        self._add(SIstationDict)

        # Sparar ändringen till xml-filen
        self._save()

    #

    def dump(self):
        """
        Skriver ut trädet till sys.stdout. För debugging.
        ( Icke-ascii ser underliga ut när de skrivs ut )
        """
        # Indenterar om self.prettyPrint == True
        if self.prettyPrint:
            self._indent(self.getroot())

        xml.etree.ElementTree.dump(self.getroot())

    #
    
    def _indent(self, elem, level=0):
        """
        Indenterar XML-filen (annars är allt på en rad)
        Ursprungligen från http://effbot.org/zone/element-lib.htm#prettyprint av Fredrik Lundh
        """
        i = "\r\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
