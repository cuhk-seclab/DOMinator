aardvark.loadObject ({

keyCommands : [],

//------------------------------------------------------------
loadCommands : function () {
if (this.keyCommands.length > 0)
  return;
// 0: name (member of this.strings, or literal string)
// 1: function
// 2: no element needed (null for element commands)
// 3: "extension" of ext only, "bookmarklet" for bm only, null for both
var keyCommands = [
  ["label element", this.addSensitive],
  ["unlabel element", this.removeSensitive],
  ["finish labeling", this.finishLabel, true],
  ["wider", this.wider],
  ["narrower", this.narrower],
  // ["undo", this.undo, true],
  ["view source", this.viewSource],
  ["quit", this.quit, true],
  ["help", this.showMenu, true],
  ];

for (var i=0; i<keyCommands.length; i++)
  this.addCommandInternal(keyCommands[i]);
},

addCommandInternal : function (a) {
  this.addCommand(a[0], a[1], a[2], a[3], a[4], true);
},

keyCommands : [],

//-----------------------------------------------------
addCommand : function (name, func,
    noElementNeeded, mode, keystroke, suppressMessage) {
if (this.isBookmarklet) {
  if (mode == "extension")
    return;
  }
else {
  if (mode == "bookmarklet")
    return;
  }
    
if (this.strings[name] && this.strings[name] != "")
  name = this.strings[name];

if (keystroke) {
  keyOffset = -1;
  console.log("LabelTool: "+keystroke);
  }
else {
  var keyOffset = name.indexOf('&');
  if (keyOffset != -1) {
    keystroke = name.charAt(keyOffset+1);
    name = name.substring (0, keyOffset) + name.substring (keyOffset+1);
    }
  else {
    keystroke = name.charAt(0);
    keyOffset = 0;
    }
  }
var command = {
    name: name,
    keystroke: keystroke,
    keyOffset: keyOffset,
    func: func
    } 
if (noElementNeeded)
  command.noElementNeeded = true; 
 
for (var i=0; i<this.keyCommands.length; i++) {
  if (this.keyCommands[i].keystroke == keystroke) {
    /*if (!suppressMessage)
      this.showMessage ("<p style='color: #000; margin: 3px 0 0 0;'>command \"<b>" + this.keyCommands[i].name + "</b>\" replaced with \"<b>" + name + "</b>\"</p>");*/
    this.keyCommands[i] = command;
    return;
    }    
  } 
if (!suppressMessage)
  this.showMessage ("<p style='color: #000; margin: 3px 0 0 0;'>command \"<b>" + name + "</b>\" added</p>");
this.keyCommands.push (command);
},

//------------------------------------------------------------
wider : function (elem) {
if (elem && elem.parentNode) {
  var newElem = this.findValidElement (elem.parentNode);
  if (!newElem)
    return false;
  
  if (this.widerStack && this.widerStack.length>0 && 
    this.widerStack[this.widerStack.length-1] == elem) {
    this.widerStack.push (newElem);
    }
  else {
    this.widerStack = [elem, newElem];
    }
  this.selectedElem = newElem;
  this.showBoxAndLabel (newElem, 
      this.makeElementLabelString (newElem));
  this.didWider = true;
  return true;
  }
return false;
},

//------------------------------------------------------------
narrower : function (elem) {
if (elem) {
  if (this.widerStack && this.widerStack.length>1 && 
    this.widerStack[this.widerStack.length-1] == elem) {
    this.widerStack.pop();
    newElem = this.widerStack[this.widerStack.length-1];
    this.selectedElem = newElem;
    this.showBoxAndLabel (newElem, 
        this.makeElementLabelString (newElem));
    this.didWider = true;
    return true;
    }
  }
return false;
},
  
//------------------------------------------------------------
quit : function () {
// alert("Quit!");
this.doc.aardvarkRunning = false;

if (this.doc.all) {
  this.doc.detachEvent ("onmouseover", this.mouseOver);
  this.doc.detachEvent ("onmousemove", this.mouseMove);
  this.doc.detachEvent ("onkeypress", this.keyDown);
  this.doc.detachEvent ("onmouseup", this.mouseUp, false);
  }
else {
  this.doc.removeEventListener("mouseover", this.mouseOver, false);
  this.doc.removeEventListener("mousemove", this.mouseMove, false);
  this.doc.removeEventListener("mouseup", this.mouseUp, false);
  this.doc.removeEventListener("keypress", this.keyDown, false);
  }

this.removeBoxFromBody ();

delete (this.selectedElem);
if (this.widerStack)
  delete (this.widerStack);
return true;
},

//------------------------------------------------------------
suspend : function () {
if (this.doc.all) {
  this.doc.detachEvent ("onmouseover", this.mouseOver);
  this.doc.detachEvent ("onkeypress", this.keyDown);
  }
else {
  this.doc.removeEventListener("mouseover", this.mouseOver, false);
  this.doc.removeEventListener("keypress", this.keyDown, false);
  }
return true;
},

//------------------------------------------------------------
resume : function () {
if (this.doc.all) {
  this.doc.attachEvent ("onmouseover", this.mouseOver);
  this.doc.attachEvent ("onkeypress", this.keyDown);
  }
else {
  this.doc.addEventListener ("mouseover", this.mouseOver, false);
  this.doc.addEventListener ("keypress", this.keyDown, false);
  }
return true;
},

//------------------------------------------------------------

viewSource : function (elem) {
var dbox = new AardvarkDBox ("#fff", true, false, false, this.strings.viewHtmlSource, true);
var v = this.getOuterHtmlFormatted(elem, 0);
dbox.innerContainer.innerHTML = v;

if (!this.doc.didViewSourceDboxCss) {
  this.createCSSRule ("div.aardvarkdbox div", "font-size: 13px; margin: 0; padding: 0;");
  this.createCSSRule ("div.aardvarkdbox div.vsblock", "font-size: 13px; border: 1px solid #ccc; border-right: 0;margin: -1px 0 -1px 1em; padding: 0;");
  this.createCSSRule ("div.aardvarkdbox div.vsline", "font-size: 13px; border-right: 0;margin: 0 0 0 .6em;text-indent: -.6em; padding: 0;");
  this.createCSSRule ("div.aardvarkdbox div.vsindent", "font-size: 13px; border-right: 0;margin: 0 0 0 1.6em;text-indent: -.6em; padding: 0;");
  this.createCSSRule ("div.aardvarkdbox span.tag", "color: #c00;font-weight:bold;");
  this.createCSSRule ("div.aardvarkdbox span.pname", "color: #080;font-weight: bold;");
  this.createCSSRule ("div.aardvarkdbox span.pval", "color:#00a;font-weight: bold;");
  this.createCSSRule ("div.aardvarkdbox span.aname", "color: #050;font-style: italic;font-weight: normal;");
  this.createCSSRule ("div.aardvarkdbox span.aval", "color:#007;font-style: italic;font-weight: normal;");
  this.doc.didViewSourceDboxCss = true;
  }
dbox.show ();
return true;
},

//------------------------------------------------------------
paste : function (o) {
if (o.parentNode != null) {
  if (this.undoData.mode == "R") {
    e = this.undoData.elem;
    if (e.nodeName == "TR" && o.nodeName != "TR") {
      var t = this.doc.createElement ("TABLE");
      var tb = this.doc.createElement ("TBODY");
      t.appendChild (tb);
      tb.appendChild (e);
      e = t;
      }
    else if (e.nodeName == "TD" && o.nodeName != "TD") {
      var t2 = this.doc.createElement ("DIV");
      
      var len = e.childNodes.length, i, a = [];
  
      for (i=0; i<len; i++)
        a[i] = e.childNodes.item(i);
        
      for (i=0; i<len; i++) {
        e.removeChild(a[i]);
        t2.appendChild (e);
        }     
      t2.appendChild (e);
      e = t2;    
      }
      
    if (o.nodeName == "TD" && e.nodeName != "TD")
      o.insertBefore (e, o.firstChild);
    else if (o.nodeName == "TR" && e.nodeName != "TR")
      o.insertBefore (e, o.firstChild.firstChild);
    else
      o.parentNode.insertBefore (e, o);
    this.clearBox ();
    this.undoData = this.undoData.next;
    }
  }
return true;
},

//--------------------------------------------------------
getOuterHtmlFormatted : function (node, indent) {
var str = "";

if (this.doc.all) {
  return "<pre>" + node.outerHTML.replace(/\</g, '&lt;').replace(/\>/g, '&gt;') + "</pre>"; 
  }
  
switch (node.nodeType) {
  case 1: // ELEMENT_NODE
    {
    if (node.style.display == 'none')
      break;
    var isLeaf = (node.childNodes.length == 0 && this.leafElems[node.nodeName]);
    var isTbody = (node.nodeName == "TBODY" && node.attributes.length == 0);
    
    if (isTbody) {
      for (var i=0; i<node.childNodes.length; i++)
        str += this.getOuterHtmlFormatted(node.childNodes.item(i), indent);
      }
    else {
      if (isLeaf)
        str += "\n<div class='vsindent'>\n";
      else if (indent>0)
        str += "\n<div class='vsblock' style=''>\n<div class='vsline'>\n";
      else
        str += "\n<div class='vsline'>\n";
      
      str += "&lt;<span class='tag'>" +
            node.nodeName.toLowerCase() + "</span>";
      for (var i=0; i<node.attributes.length; i++) {
        if (node.attributes.item(i).nodeValue != null &&
          node.attributes.item(i).nodeValue != '') {
          str += " <span class='pname'>"
          str += node.attributes.item(i).nodeName;
          
          if (node.attributes.item(i).nodeName == "style") {
            var styles = "";
            var a = node.attributes.item(i).nodeValue.split(";");
            for (var j=0; j<a.length; j++) {
              var pair = a[j].split (":");
              if (pair.length == 2) {
                var s = this.trimSpaces(pair[0]), index;
                styles += "; <span class='aname'>" + s + "</span>: <span class='aval'>" + this.trimSpaces(pair[1]) + "</span>";
                }
              }
            styles = styles.substring (2);
            str += "</span>=\"" +  styles + "\"";
            }
          else {
            str += "</span>=\"<span class='pval'>" +  node.attributes.item(i).nodeValue + "</span>\"";
            }
          }
        }
      if (isLeaf)
        str += " /&gt;\n</div>\n";
      else {
        str += "&gt;\n</div>\n";
        for (var i=0; i<node.childNodes.length; i++)
          str += this.getOuterHtmlFormatted(node.childNodes.item(i), indent+1);
        str += "\n<div class='vsline'>\n&lt;/<span class='tag'>" +
          node.nodeName.toLowerCase() + "</span>&gt;\n</div>\n</div>\n"
        }
      }
    }
    break;
      
  case 3: //TEXT_NODE
    {
    var v = node.nodeValue;
    v = v.replace ("<", "&amp;lt;").replace (">", "&amp;gt;"); 
    
    v = this.trimSpaces (v);
    if (v != '' && v != '\n' 
        && v != '\r\n' && v.charCodeAt(0) != 160)
      str += "<div class='vsindent'>" + v + "</div>";
    }
    break;
    
  case 4: // CDATA_SECTION_NODE
    str += "<div class='vsindent'>&lt;![CDATA[" + node.nodeValue + "]]></div>";
    break;
        
  case 5: // ENTITY_REFERENCE_NODE
    str += "&amp;" + node.nodeName + ";<br>"
    break;

  case 8: // COMMENT_NODE
    str += "<div class='vsindent'>&lt;!--" + node.nodeValue + "--></div>"
    break;
  }
return str;
},

camelCaseProps : {
  'colspan': 'colSpan',
  'rowspan': 'rowSpan',
  'accesskey': 'accessKey',
  'class': 'className',
  'for': 'htmlFor',
  'tabindex': 'tabIndex',
  'maxlength': 'maxLength',
  'readonly': 'readOnly',
  'frameborder': 'frameBorder',
  'cellspacing': 'cellSpacing',
  'cellpadding': 'cellPadding'
},

//--------------------------------------------------------
domJavascript : function (node, indent) {
var indentStr = "";
for (var c=0; c<indent; c++)
  indentStr += "  ";
  
switch (node.nodeType) {
  case 1: // ELEMENT_NODE
    {
    if (node.style.display == 'none')
      break;
      
    var isLeaf = (node.childNodes.length == 0 && this.leafElems[node.nodeName]);  
    
    var children = "", numChildren = 0, t, useInnerHTML = false;
    if (!isLeaf) {
      for (var i=0; i<node.childNodes.length; i++) {
        t = this.domJavascript(node.childNodes.item(i), indent+1);
        if (t == "useInnerHTML") {
          useInnerHTML = true;
          break;
          }
        if (t) {
          children += indentStr + "  " + t + ",\n";
          numChildren++;
          }
        }
      //  children = indentStr + "   [\n" + children.substring(0, children.length-2) + "\n" + indentStr + "   ]\n"; 
      if (numChildren && !useInnerHTML)
        children = children.substring(0, children.length-2) + "\n"; 
      }

    var properties = "", styles = "", numProps = 0, sCount = 0;
    
    for (var i=0; i<node.attributes.length; i++) {
      if (node.attributes.item(i).nodeValue != null && node.attributes.item(i).nodeValue != '') {
        var n = node.attributes.item(i).nodeName,
           v = node.attributes.item(i).nodeValue;
          
        switch (n) {
          case "style": {
            var a = node.attributes.item(i).nodeValue.split(";");
            for (var j=0; j<a.length; j++) {
              var pair = a[j].split (":");
              if (pair.length == 2) {
                var s = this.trimSpaces(pair[0]), index;
                while ((index = s.indexOf("-")) != -1)
                 s = s.substring(0, index) + s.charAt(index+1).toUpperCase() + s.substring(index+2);
                 
                if (s == "float") { // yuk
                 styles += ", <span style='color:#060; font-style:italic'>styleFloat</span>: \"<span style='color:#008;font-style:italic'>" + this.trimSpaces(pair[1]) + "</span>\", <span style='color:#060; font-style:italic'>cssFloat</span>: \"<span style='color:#008;font-style:italic'>" + this.trimSpaces(pair[1]) + "</span>\"";
                 }
                else {
                 styles += ", <span style='color:#060; font-style:italic'>" + s + "</span>: \"<span style='color:#008;font-style:italic'>" + this.trimSpaces(pair[1]) + "</span>\"";
                 }
                sCount++;
                }
              }
            styles = styles.substring (2);
            break;
            }
          default:
            {
            var newN;
            if ((newIn = this.camelCaseProps[n]) != null)
              n = newIn;
            properties += ", <span style='color:#080;font-weight: bold'>" + n + "</span>:\"<span style='color:#00b;font-weight: bold'>" + v + "</span>\"";
            numProps++;
            break;
            }
          }
        }
      }
      
    if (useInnerHTML) {
      var ih = node.innerHTML, index;
      
      if ((index = ih.indexOf("useInnerHTML")) != -1) {
        ih = ih.substring(index + "useInnerHTML".length);
        if (index = ih.indexOf("->") != -1)
          ih = ih.substring(index+3);
        }
      
      properties += ", <span style='color:#080;font-weight: bold'>innerHTML</span>:\"<span style='color:#00b;font-weight: bold'>" +  this.escapeForJavascript (ih) + "</span>\"";
      numProps++;      
      numChildren = 0;
      }
      
    if (styles != "") {
      properties = "{<span style='color:#080;font-weight: bold'>style</span>:{" + styles + "}" + properties + "}";
      numProps++;
      }
    else
      properties = "{" + properties.substring(2) + "}";
    
    // element does not start with an indent, does not end with a linefeed or comma
    // children string starts with indent, has indent for each child

    str = "<span style='color:red;font-weight:bold'>" + node.nodeName + "</span> (";

    if (numChildren)
      if (numProps)
        return str + properties + ",\n" + children + indentStr + ")";
      else
        return str + "\n" + children + indentStr + ")";
    else
      if (numProps)
        return str + properties  + ")";
      else
        return str + ")";
    }
    break;
      
  case 3: //TEXT_NODE
    {
    var n = node.nodeValue;
    if (node.nodeValue != '')
      n = this.escapeForJavascript (n);   
      
    n = this.trimSpaces (n);
    if (n.length > 0)
      return "\"<b>" + n + "</b>\"";
    }
    break;
    
  case 4: // CDATA_SECTION_NODE
    break;
        
  case 5: // ENTITY_REFERENCE_NODE
    break;

  case 8: // COMMENT_NODE
    if (node.nodeValue.indexOf("useInnerHTML") != -1)
      return "useInnerHTML";
    break;
  }
return null;
},

//-------------------------------------------------
undo : function () {
if (this.undoData == null)
  return false;

this.clearBox ();
var ud = this.undoData;
switch (ud.mode) {
  case "I": {
    var a = [];
    var len = this.doc.body.childNodes.length, i, count = 0, e;
    
    for (i=0; i<len; i++)
      {
      e = this.doc.body.childNodes.item (i);
      if (!e.isAardvark)
        {
        a[count] = e;
        count++;
        }
      }
    for (i=count-1; i>=0; i--)
      this.doc.body.removeChild (a[i]);
      
    len = this.undoData.numElems;
    for (i=0; i<len; i++)
      this.doc.body.appendChild (this.undoData[i]);

    this.doc.body.style.background = this.undoData.bg;
    this.doc.body.style.backgroundColor = this.undoData.bgc;
    this.doc.body.style.backgroundImage = this.undoData.bgi;
    this.doc.body.style.margin = this.undoData.m;
    this.doc.body.style.textAlign = this.undoData.ta;
    break;
    }
  case "R": {
    if (ud.nextSibling)
      ud.parent.insertBefore (ud.elem, ud.nextSibling);
    else
      ud.parent.appendChild (ud.elem);
    break;
    }
  default:
    return false;
  }
this.undoData = this.undoData.next; 
return true;
},

//-------------------------------------------------
showMenu : function () {
if(window.Logger)Logger.write(this.helpBoxId);
if (this.helpBoxId != null) {
  if (this.killDbox (this.helpBoxId) == true) {
    delete (this.helpBoxId);
    return;
    }
  }
var s = "<table style='margin:5px 10px 0 10px'>";
for (var i=0; i<this.keyCommands.length; i++) {
  s += "<tr><td style='padding: 3px 7px; border: 1px solid black; font-family: courier; font-weight: bold;" +
    "background-color: #fff'>" + this.keyCommands[i].keystroke +
    "</td><td style='padding: 3px 7px; font-size: .9em;  text-align: left;'>" + this.keyCommands[i].name + "</td></tr>";
  }
s += "</table><br>" + this.strings.LabelToolInfo; 
  
var dbox = new AardvarkDBox ("#fff2db", true, true, true, this.strings.aardvarkKeystrokes);
dbox.innerContainer.innerHTML = s;
dbox.show ();
this.helpBoxId = dbox.id;
return true;
},


//------------------------------------------------------------
getByKey : function (key) {
var s = key + " - ";
for (var i=0; i<this.keyCommands.length; i++) {
    s += this.keyCommands[i].keystroke;
    if (this.keyCommands[i].keystroke == key) {
        return this.keyCommands[i];
        }
    }
return null;
},

addSensitive: function(elem) {
  // alert("add?");
  function changeCPP(elem){
    if (confirm('Are you sure you want to label this element as sensitive?\n: '+elem.outerHTML)) {
      // elem.setAttribute("cpp_protected","1");
      aardvark.labelSens(elem);
      console.log("event"+elem.getAttribute("nid"));
    } else {
      // Do nothing!
      console.log('Nothing happened');
      elem.style.backgroundColor = "";
    }
    clearTimeout(window.countdown);
  }
  changeCPP(elem);
},

//------------------------------------------------------------
removeSensitive : function (elem) {
  if (!elem.getAttribute("cpp_protected")){
    return;
  }
  function removeCPP(elem){
    if (confirm('Are you sure you want to remove this element from sensitive tags?\nContent: '+elem.outerHTML)) {
      aardvark.unlabelSens(elem);
      console.log("event"+elem.getAttribute("nid"));
    } else {
      // Do nothing!
      console.log('Nothing happened');
      elem.style.backgroundColor = "";
    }
    clearTimeout(window.countdown);
  }
  // elem.style.backgroundColor = "blue";
  window.countdown = setTimeout(function(){removeCPP(elem);}, 500);
},

finishLabel: function() {
  console.log("[LabelTool] finish");
  els = document.querySelectorAll("[cpp_protected='1']");
  contents=[]
  errors=["!!!\n!Errors: \n"]
  els.forEach(function(entry) {
    console.log("LabelTool"+ entry.getAttribute("nid")+"\n");
    // contents.push(entry.outerHTML+"\n");
    selector = aardvark.unique(entry);
    if (selector){
      contents.push(selector+"\n");
    }
    else{
      errors.push(entry.outerHTML+"\n");
    }
  });
  this.saveFile(contents.concat(errors), "SensTag.log");
  this.saveFile([document.documentElement.outerHTML], "page.html");
},

saveFile: function (Content, filename) {
  // alert()
  htmlContent=Content;
  var bl = new Blob(htmlContent, {type: "text/html"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(bl);
  a.download = filename;
  a.hidden = true;
  document.body.appendChild(a);
  a.click();
},

//--------------------------------------------------------
showMessage : function (s) {
  var dbox = new AardvarkDBox ("#feb", false, true, true);
  dbox.innerContainer.innerHTML = s;
  dbox.show ();
  setTimeout ("aardvark.killDbox(" + dbox.id + ")", 2000);
},

//--------------------------------------------------------
getNextElement : function () {
this.index++;
if (this.index < this.list.length) {
  this.depth = this.list[this.index].depth;
  return this.list[this.index].elem;
  }
return null;
},

//--------------------------------------------------------
tree : function () {
var t = {
  list: [{elem: this, depth: 0}],
  index: -1,
  depth: 0,
  next: aardvark.getNextElement
  };
aardvark.addChildren (this, t, 1);
return t;
},

//--------------------------------------------------------
addChildren : function (elem, t, depth) {
  for (var i=0; i<elem.childNodes.length; i++) {
    var child = elem.childNodes[i];
    if (child.nodeType == 1) {
      t.list.push({elem: child, depth: depth});
      if (child.childNodes.length != 0 && !aardvark.leafElems[child.nodeName])
        aardvark.addChildren(child, t, depth + 1);
      }
    }
  }

});
