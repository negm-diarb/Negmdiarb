from pathlib import Path
import re
p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def rm(src,name,repl):
 sig="    void "+name+"("
 a=src.find(sig)
 if a<0: raise SystemExit("method not found: "+name)
 b=src.find("{",a); d=0
 for i in range(b,len(src)):
  if src[i]=="{": d+=1
  elif src[i]=="}":
   d-=1
   if d==0: return src[:a]+repl+"\n"+src[i+1:]
 raise SystemExit("unbalanced: "+name)

s=rm(s,"addBusinessCard",r'''    void addBusinessCard(DocumentSnapshot d){
        LinearLayout card=box();
        String n=safe(d.getString("name")); double avg=num(d,"ratingAvg");
        long cnt=d.getLong("ratingCount")==null?0:d.getLong("ratingCount");
        String badge=truth(d,"featured")?" ⭐ مميز":"";
        TextView title=tv("🏪 "+n+badge); title.setTextSize(18); title.setTypeface(null,android.graphics.Typeface.BOLD); title.setTextColor(Color.rgb(16,42,102)); card.addView(title);
        TextView meta=tv("📂 "+safe(d.getString("category"))); meta.setTextSize(13); meta.setTextColor(Color.rgb(104,115,134)); card.addView(meta);
        card.addView(buildStarsRow(avg,cnt,false));
        String desc=safe(d.getString("description")); if(desc.length()>100)desc=desc.substring(0,100)+"…";
        card.addView(tv("📍 "+safe(d.getString("address"))+(desc.isEmpty()?"":"\n"+desc)));
        LinearLayout r1=new LinearLayout(this); r1.setOrientation(LinearLayout.HORIZONTAL);
        Button map=btn("🗺️ خريطة"), callb=btn("📞 اتصال"), wa=btn("💬 واتساب");
        for(Button x:new Button[]{map,callb,wa}){x.setTextSize(12);x.setAllCaps(false);x.setMinWidth(0);x.setPadding(0,0,0,0);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(0,dp(46),1);q.setMargins(dp(2),dp(2),dp(2),dp(2));r1.addView(x,q);} card.addView(r1);
        LinearLayout r2=new LinearLayout(this); r2.setOrientation(LinearLayout.HORIZONTAL);
        Button rate=btn("⭐ تقييم"), fav=btn(favoriteIds.contains(d.getId())?"♥ حفظ":"♡ حفظ"), share=btn("↗ مشاركة");
        for(Button x:new Button[]{rate,fav,share}){x.setTextSize(12);x.setAllCaps(false);x.setMinWidth(0);x.setPadding(0,0,0,0);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(0,dp(44),1);q.setMargins(dp(2),0,dp(2),dp(2));r2.addView(x,q);} card.addView(r2);
        card.setOnClickListener(v->{logEvent("businessViews",d.getId());showBusinessDetails(d);});
        map.setOnClickListener(v->{logEvent("mapClicks",d.getId());openMap(d);});
        callb.setOnClickListener(v->{logEvent("callClicks",d.getId());call(d.getString("phone"));});
        wa.setOnClickListener(v->{logEvent("whatsappClicks",d.getId());wa(d.getId(),d.getString("whatsapp"));});
        rate.setOnClickListener(v->showRatingDialog(d.getId())); fav.setOnClickListener(v->toggleFavorite(d.getId(),fav)); share.setOnClickListener(v->shareBusiness(d));
        businessList.addView(card);
    }''')

s=rm(s,"loadRatings",r'''    void loadRatings(){
        adminRatingList.removeAllViews(); if(!isMainAdmin()){addText(adminRatingList,"التقييمات متاحة للمدير الرئيسي فقط.");return;}
        db.collection("ratings").limit(300).get().addOnSuccessListener(snap->{
            if(snap.isEmpty()){addText(adminRatingList,"لا توجد تقييمات.");return;}
            for(DocumentSnapshot d:snap){
                String bid=safe(d.getString("businessId")); String saved=safe(d.getString("businessName"));
                Long stars=d.getLong("stars"); String status=safe(d.getString("status"));
                LinearLayout c=box(); TextView h=tv("🏪 "+(saved.isEmpty()?"جاري تحميل اسم المنشأة…":saved)); h.setTextSize(17); h.setTypeface(null,android.graphics.Typeface.BOLD); c.addView(h);
                c.addView(tv("⭐ "+(stars==null?"":stars)+" من 5\n"+safe(d.getString("text"))+"\nالحالة: "+status));
                if(!bid.isEmpty())db.collection("businesses").document(bid).get().addOnSuccessListener(bs->{String real=safe(bs.getString("name"));if(!real.isEmpty())h.setText("🏪 "+real);});
                Button a=btn("pending".equals(status)?"اعتماد ✅":"حذف 🗑️");a.setAllCaps(false);c.addView(a);
                a.setOnClickListener(v->{if("pending".equals(d.getString("status")))approveRating(d);else d.getReference().delete().addOnSuccessListener(x->loadRatings());});
                adminRatingList.addView(c);
            }
        }).addOnFailureListener(e->addText(adminRatingList,"تعذر تحميل التقييمات: "+safe(e.getMessage())));
    }''')

if "boolean adminReturnToPanel" not in s:s=s.replace("    void installBackHandler()","    boolean adminReturnToPanel=false;\n\n    void installBackHandler()",1)
if "void returnToAdmin()" not in s:
 s=s.replace("    void installBackHandler()", "    void returnToAdmin(){show(adminPanel);refreshAdminBadges();}\n\n    void installBackHandler()", 1)\ns=rm(s,"installBackHandler",r'''    void installBackHandler(){
        getOnBackPressedDispatcher().addCallback(this,new OnBackPressedCallback(true){
            @Override public void handleOnBackPressed(){
                if(addPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel)returnToAdmin();else showHome();return;}
                if(offersPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel)returnToAdmin();else showHome();return;}
                if(adminPanel.getVisibility()==View.VISIBLE){new AlertDialog.Builder(MainActivity.this).setTitle("العودة من لوحة المدير").setMessage("هل تريد العودة للرئيسية؟").setNegativeButton("إلغاء",null).setPositiveButton("الرئيسية",(d,w)->showHome()).show();return;}
                if(homePanel.getVisibility()==View.VISIBLE){new AlertDialog.Builder(MainActivity.this).setTitle("الخروج من نجم ديرب").setMessage("هل تريد الخروج من التطبيق؟").setNegativeButton("إلغاء",null).setPositiveButton("خروج",(d,w)->finish()).show();}else showHome();
            }
        });
    }''')

s=s.replace("adminReturnSection=R.id.businessSection;clearForm();show(addPanel);","adminReturnSection=R.id.businessSection;adminReturnToPanel=true;clearForm();show(addPanel);")
s=s.replace("adminReturnSection=R.id.offerSection;openAdminOfferForm();","adminReturnSection=R.id.offerSection;adminReturnToPanel=true;openAdminOfferForm();")
s=s.replace("adminReturnSection=R.id.businessSection;editingBusinessId=d.getId();fillBusiness(d);show(addPanel);","adminReturnSection=R.id.businessSection;adminReturnToPanel=true;editingBusinessId=d.getId();fillBusiness(d);show(addPanel);")
s=s.replace('findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(adminMode)returnToAdmin();else showHome();});','findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(adminReturnToPanel)returnToAdmin();else showHome();});')
s=s.replace('findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(adminMode)returnToAdmin();else showHome();});','findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(adminReturnToPanel)returnToAdmin();else showHome();});')

listener=r'''    com.google.firebase.firestore.ListenerRegistration adminNotificationListener;
    void startAdminNotificationListener(){
        if(!isMainAdmin()||db==null)return;
        if(adminNotificationListener!=null)adminNotificationListener.remove();
        adminNotificationListener=db.collection("adminNotifications").whereEqualTo("status","pending").addSnapshotListener((snap,e)->{
            if(e!=null||snap==null)return;
            if(!snap.isEmpty())postAdminLocalNotification("نجم ديرب — مراجعة مطلوبة","يوجد "+snap.size()+" عنصر يحتاج مراجعة.");
            refreshAdminBadges();
        });
    }

'''
if "startAdminNotificationListener()" not in s:
 s=s.replace("    void returnToAdmin(){",listener+"    void returnToAdmin(){",1)
s=s.replace("if(isMainAdmin()){initAdminNotifications();loadAdminStats();refreshAdminBadges();}","if(isMainAdmin()){initAdminNotifications();loadAdminStats();refreshAdminBadges();startAdminNotificationListener();}")
p.write_text(s,encoding="utf-8")
print("V30 patch applied")
