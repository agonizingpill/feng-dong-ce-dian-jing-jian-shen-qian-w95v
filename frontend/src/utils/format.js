export const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fixed=(x,d=3)=>x==null?'—':Number(x).toFixed(d);
export const formData=form=>Object.fromEntries(new FormData(form));
