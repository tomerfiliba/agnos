package agnos.util;

import java.io.File;
import java.io.IOException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.xml.sax.SAXException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;


class HeteroMapLoader
{
	public class HeteroMapLoadingException extends Exception
	{
		public HeteroMapLoadingException(String message)
		{
			super(message);
		}
	}
	
	static public HeteroMap fromFile(String filename) throws IOException, SAXException, 
			ParserConfigurationException, HeteroMapLoadingException
	{
		  File file = new File(filename);
		  DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		  DocumentBuilder db = dbf.newDocumentBuilder();
		  Document doc = db.parse(file);
		  doc.getDocumentElement().normalize();
		  Element root = doc.getDocumentElement();
		  return fromXML(root);
	}
	
	static public HeteroMap fromXML(Element root) throws HeteroMapLoadingException
	{
		HeteroMap hmap = new HeteroMap();
		recFromXML(hmap, root);
		return hmap;
	}
	
	static private void recFromXML(HeteroMap hmap, Element elem) throws HeteroMapLoadingException
	{
		if (elem.getNodeType() != Node.ELEMENT_NODE) {
			return;
		}
		/*String tag = elem.getNodeName();
		if (tag.equals("hmap")) {
			HeteroMap hmaps2 = hamp.putNewMap(elem.getAttribute("name"));
			NodeList nodes = elem.getChildNodes();
			for (int i = 0; i < nodes.getLength(); i++) {
				Node n = nodes.item(i);
				recFromXML(hmap2, n);
			}
		}
		else if (tag.equals("int")) {
			int val = Integer.parseInt(elem.getAttribute("value"));
			hamp.put(elem.getAttribute("name"), val);
		}
		else if (tag.equals("str")) {
			hamp.put(elem.getAttribute("name"), elem.getAttribute("value"));
		}
		else if (tag.equals("buffer")) {
			hamp.put(elem.getAttribute("name"), elem.getAttribute("value"));
		}
		else if (tag.equals("bool")) {
			hamp.put(elem.getAttribute("name"), elem.getAttribute("value").equals("true"));
		}
		else if (tag.equals("list")) {
			hamp.put(elem.getAttribute("name"), lst);
			NodeList nodes = elem.getChildNodes();
			for (int i = 0; i < nodes.getLength(); i++) {
				Node n = nodes.item(i);
				recFromXML(hmap2, n);
			}
		}
		else {
			throw new LoadingException("invalid tag: " + tag);
		}*/
	}
}








