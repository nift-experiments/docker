"""Docker's discovery outputs over explicit published page metadata."""
import json

def outputs(root,model):
 base=model['base_url'];text='# Docker Documentation full text\n\n> Source index: '+base+'/llms.txt\n> This file contains page metadata and stable markdown URLs for bulk ingestion.'
 for row in model['llms_pages']:
  route=row['url'].removeprefix(base);page=model['pages'].get(route);title=page['title'] if page and page['title']!=row['title'].rstrip() else row['title'];description=row.get('description','')
  if 'description' in model.get('changes',{}).get(route,{}) and page:description=next((v['content'] for v in page['meta'] if v.get('name')=='description'),'')
  markdown=page['markdown'] if page else row['markdown']
  text+='\n\n## '+title+'\nURL: '+row['url']+'\nMarkdown: '+markdown
  if description:text+='\nDescription: '+description.replace('\n',' ')
 text+='\n'
 # The narrative and editorial grouping remain a maintained text template.
 # Page labels/descriptions have explicit metadata bindings.
 guide=(root/'publication/templates/llms.txt').read_text()
 seed=json.loads((root/'data/publication.json').read_text())
 for route,delta in model.get('changes',{}).items():
  old=seed['pages'][route];new=model['pages'][route]
  if 'title' in delta:guide=guide.replace('['+old['title']+']('+base+route+')','['+new['title']+']('+base+route+')')
  if 'description' in delta:
   before=next((v['content'] for v in old['meta'] if v.get('name')=='description'),'');after=next((v['content'] for v in new['meta'] if v.get('name')=='description'),'')
   if before:guide=guide.replace(before,after)
 return {'llms.txt':guide,'llms-full.txt':text}
