"""HTML → Markdown downloads, using maintained/composed HTML without an MD parser.

Small explicit Docker export rules remove controls and preserve code payloads,
all tab panels, links, images, tables and alert text. This is publication work,
measured separately from composition; it is not a Markdown renderer.
"""
from html.parser import HTMLParser
from dataclasses import dataclass,field
import re,base64,json
@dataclass
class Node:
 tag:str;attrs:dict=field(default_factory=dict);children:list=field(default_factory=list)
 def text(self):return ''.join(v if isinstance(v,str) else v.text() for v in self.children)
class Document(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self,value):
  super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root];self.feed(value)
 def handle_starttag(self,tag,attrs):
  n=Node(tag,dict(attrs));self.stack[-1].children.append(n)
  if tag not in self.VOID:self.stack.append(n)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in self.VOID:self.stack.pop()
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:del self.stack[i:];break
 def handle_data(self,value):self.stack[-1].children.append(value)
def descendants(n,tag):
 for c in n.children:
  if isinstance(c,Node):
   if c.tag==tag:yield c
   yield from descendants(c,tag)
def convert(value,title=None):
 root=Document(value).root;code_blocks=[]
 def children(n):return ''.join(render(c) for c in n.children)
 def render(n):
  if isinstance(n,str):return re.sub(r'\s+',' ',n)
  tag=n.tag;attrs=n.attrs;classes=attrs.get('class','').split()
  if tag=='div' and ('data-export-code' in attrs or attrs.get('x-ref')=='root'):
   payload=attrs.get('data-export-code');language='goat' if 'goat' in classes else ''
   codes=list(descendants(n,'code'));chosen=next((c for c in codes if c.attrs.get('data-lang')),None)
   if chosen:language=chosen.attrs['data-lang']
   if not payload:
    for button in descendants(n,'button'):
     if 'data-export-code' in button.attrs:payload=button.attrs['data-export-code'];break
     match=re.search(r"code:\s*'([A-Za-z0-9+/=]*)'",button.attrs.get('x-data',''))
     if match:payload=match.group(1);break
   if payload is not None:
    raw=base64.b64decode(payload).decode();fence='`'*max(3,max((len(m.group())+1 for m in re.finditer(r'`+',raw)),default=3));token='\ue000'+str(len(code_blocks))+'\ue001';code_blocks.append((token,fence+language+'\n'+raw.rstrip('\n')+'\n'+fence));return '\n\n'+token+'\n\n'
  if tag in ['script','style','svg','template','select','input'] or attrs.get('role')=='tooltip':return ''
  if tag=='button':return '\n\n**'+n.text().strip()+'**\n\n' if 'tab-item' in classes else ''
  if tag=='pre':
   if 'mermaid' in classes:code=n.text();language='mermaid'
   else:
    codes=list(descendants(n,'code'));chosen=next((c for c in codes if 'language-' in c.attrs.get('class','')),codes[-1] if codes else n);code=chosen.text();language=chosen.attrs.get('data-lang','')
    if not language:
     match=re.search(r'(?:^|\s)language-(\S+)',chosen.attrs.get('class',''));language=match.group(1) if match else ''
   fence='`'*max(3,max((len(m.group())+1 for m in re.finditer(r'`+',code)),default=3));block=fence+language+'\n'+code.rstrip('\n')+'\n'+fence;token='\ue000'+str(len(code_blocks))+'\ue001';code_blocks.append((token,block));return '\n\n'+token+'\n\n'
  if tag=='code':
   text=n.text();delimiter='`'*max(1,max((len(m.group())+1 for m in re.finditer(r'`+',text)),default=1));padding=' ' if text.startswith('`') or text.endswith('`') else '';return delimiter+padding+text+padding+delimiter
  if tag=='table':
   rows=[]
   for row in descendants(n,'tr'):
    cells=[c for c in row.children if isinstance(c,Node) and c.tag in ['td','th']];rows.append([children(c).strip().replace('\n','<br>').replace('|','\\|') for c in cells])
   if not rows:return ''
   width=max(map(len,rows));lines=['| '+' | '.join(row+['']*(width-len(row)))+' |' for row in rows];lines.insert(1,'| '+' | '.join(['---']*width)+' |');return '\n\n'+'\n'.join(lines)+'\n\n'
  if tag=='blockquote':
   kind=next((c.removeprefix('admonition-') for c in classes if c.startswith('admonition-')),'');body=next((c for c in n.children if isinstance(c,Node) and 'admonition-content' in c.attrs.get('class','').split()),n);body=children(body).strip();return '\n\n'+('> '+base64.b64decode(attrs['data-export-alert-marker']).decode()+'\n>\n' if 'data-export-alert-marker' in attrs else ('> [!'+kind.upper()+']\n>\n' if kind else ''))+'\n'.join('> '+line for line in body.splitlines())+'\n\n'
  if tag in ['h1','h2','h3','h4','h5','h6']:return '\n\n'+'#'*int(tag[1])+' '+children(n).strip()+'\n\n'
  if tag=='a':
   body=children(n);href=attrs.get('href');
   if not href or 'text-black' in classes or attrs.get('aria-hidden')=='true':return body
   return '['+body.strip()+']('+href.replace(' ','%20')+')'
  if tag=='img':return '!['+attrs.get('alt','')+']('+attrs.get('src','').replace(' ','%20')+')'
  if tag=='br':return '<br>'
  if tag=='hr':return '\n\n---\n\n'
  if tag in ['strong','b']:return '**'+children(n)+'**'
  if tag in ['em','i']:return '*'+children(n)+'*'
  if tag in ['s','del']:return '~~'+children(n)+'~~'
  if tag in ['ul','ol']:
   items=[c for c in n.children if isinstance(c,Node) and c.tag=='li'];lines=[]
   for i,c in enumerate(items):
    lines2=children(c).strip().splitlines();prefix=str(i+1)+'. ' if tag=='ol' else '- ';lines.append(prefix+('\n'+' '*len(prefix)).join(lines2))
   return '\n\n'+'\n'.join(lines)+'\n\n'
  if tag in ['p','div','section','article','details','summary','dt','dd','figure']:return '\n\n'+children(n).strip()+'\n\n'
  return children(n)
 text=render(root);text=re.sub(r'\n[ \t]+\n','\n\n',text);text=re.sub(r'\n{3,}','\n\n',text).strip()
 if title and not text.startswith('# '):text='# '+title+'\n\n'+text
 for token,block in code_blocks:
  # Parent lists/quotes indent the placeholder. Apply that same container
  # prefix to every payload/fence line when restoring the protected block.
  pattern=r'(?m)^([ \t]*(?:> ?[ \t]*)*)((?:[-+*]|[0-9]+[.)]) )?'+re.escape(token)+r'$'
  def restore(m):
   prefix=m.group(1);marker=m.group(2) or '';lines=block.split('\n');continuation=prefix+' '*len(marker)
   return prefix+marker+lines[0]+''.join('\n'+continuation+line for line in lines[1:])
  text=re.sub(pattern,restore,text)
  text=text.replace(token,block)
 contracts=[]
 for node in descendants(root,'template'):
  if 'data-export-contracts' in node.attrs:contracts.extend(json.loads(base64.b64decode(node.attrs['data-export-contracts'])))
 if contracts:text+='\n\n## Raw contract details\n\n'+'\n\n'.join('```json\n'+v+'\n```' for v in dict.fromkeys(contracts))
 return text+'\n'
