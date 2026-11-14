const key='flowers-cart';
function cart(){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch(e){return[]}}
function save(v){localStorage.setItem(key,JSON.stringify(v));update();renderCart()}
function update(){const n=cart().reduce((s,x)=>s+x.qty,0);document.querySelectorAll('#cart-count').forEach(x=>x.textContent=n)}
function add(b){const c=cart(),old=c.find(x=>x.id===b.dataset.id);old?old.qty++:c.push({id:b.dataset.id,name:b.dataset.name,price:+b.dataset.price,qty:1});save(c);const t=b.innerHTML;b.textContent='Добавлено ✓';setTimeout(()=>b.innerHTML=t,900)}
function renderCart(){
  const root=document.querySelector('#cart-root');if(!root)return;
  const c=cart();
  if(!c.length){root.innerHTML='<div class="panel"><h2>Корзина пока пуста</h2><p>Добавьте букет в каталоге, и он появится здесь.</p><a class="button" href="/?page=catalog">Перейти в каталог</a></div>';return}
  const total=c.reduce((s,x)=>s+x.price*x.qty,0);
  root.innerHTML='<div class="panel cart-list">'+c.map(x=>'<div class="cart-row"><div><h2>'+x.name+'</h2><p>'+x.price.toFixed(0)+' ₽ за букет</p></div><div class="qty"><button data-cart="minus" data-id="'+x.id+'">−</button><b>'+x.qty+'</b><button data-cart="plus" data-id="'+x.id+'">+</button></div><strong>'+(x.price*x.qty).toFixed(0)+' ₽</strong><button class="remove" data-cart="remove" data-id="'+x.id+'">Удалить</button></div>').join('')+'</div><form id="checkout-form" class="form"><label>Адрес доставки<input name="delivery_address" required placeholder="Адрес доставки"></label><label>Дата доставки<input name="delivery_date" type="date" required></label><div class="cart-total"><h2>Итого: '+total.toFixed(0)+' ₽</h2><button class="button" type="submit">Оформить заказ</button><button class="button outline" type="button" data-cart="clear">Очистить</button></div><p id="checkout-message" role="status"></p></form>';
}
document.addEventListener('click',e=>{
  const addBtn=e.target.closest('.add');if(addBtn){add(addBtn);return}
  const b=e.target.closest('[data-cart]');if(!b)return;
  const id=b.dataset.id,c=cart(),i=c.findIndex(x=>x.id===id);
  if(b.dataset.cart==='plus'&&i>=0)c[i].qty++;
  if(b.dataset.cart==='minus'&&i>=0){c[i].qty--;if(c[i].qty<1)c.splice(i,1)}
  if(b.dataset.cart==='remove'&&i>=0)c.splice(i,1);
  if(b.dataset.cart==='clear')c.length=0;
  save(c);
});
document.addEventListener('submit',async e=>{
  if(e.target.id!=='checkout-form')return;
  e.preventDefault();
  const form=e.target,message=form.querySelector('#checkout-message');
  const payload={delivery_address:form.elements.delivery_address.value,delivery_date:form.elements.delivery_date.value,items:cart().map(x=>({id:+x.id,qty:x.qty}))};
  try{
    const response=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const result=await response.json();
    if(!response.ok){message.textContent=result.error||'Заказ не оформлен';if(response.status===401)message.innerHTML='Сначала <a href="/?page=login">войдите в аккаунт</a>.';return}
    save([]);location.href='/?page=account';
  }catch(_error){message.textContent='Не удалось связаться с сервером. Попробуйте ещё раз.'}
});
update();renderCart();
