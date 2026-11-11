document.addEventListener('DOMContentLoaded',()=>{const b=document.querySelector('.toggle'),m=document.getElementById('mnav');
b.addEventListener('click',()=>{const o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!o));m.classList.toggle('open',!o);m.hidden=o;b.querySelector('span').textContent=o?'Menu':'Close'});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&b.getAttribute('aria-expanded')==='true'){b.click();b.focus()}})});
