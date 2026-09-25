from pathlib import Path
import re

p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def need(old,new,label):
    global s
    if old not in s:
        raise SystemExit("MISSING: "+label)
    s=s.replace(old,new,1)

# Keep the V30 UI and authentication untouched. Only repair the requested behaviors.

# 1) Admin add/edit screens must return to the admin panel, not home.
if "boolean adminReturnToPanel" not in s:
    s=s.replace("boolean adminMode=false;", "boolean adminMode=false; boolean adminReturnToPanel=false;", 1)

# Normalize whichever V30/V29 listener form exists.
if 'findViewById(R.id.btnAdminAddBusiness).setOnClickListener' not in s:
    raise SystemExit("MISSING: admin add business listener")
s=re.sub(
    r'findViewById\(R\.id\.btnAdminAddBusiness\)\.setOnClickListener\(v->\{if\(isMainAdmin\(\)\)\{clearForm\(\);show\(addPanel\);\}else toast\("[^"]*"\);\}\);',
    'findViewById(R.id.btnAdminAddBusiness).setOnClickListener(v->{if(isMainAdmin()){adminReturnToPanel=true;clearForm();show(addPanel);}else toast("هذه الصلاحية للمدير الرئيسي فقط.");});',
    s,count=1
)

if 'findViewById(R.id.btnBackAdd).setOnClickListener' not in s:
    raise SystemExit("MISSING: back add listener")
s=re.sub(
    r'findViewById\(R\.id\.btnBackAdd\)\.setOnClickListener\([^;]+;\);',
    'findViewById(R.id.btnBackAdd).setOnClickListener(v->{if(adminReturnToPanel || adminMode){adminReturnToPanel=false;returnToAdmin();}else showHome();});',
    s,count=1
)

# Hardware back must use the explicit flag.
if "if(addPanel.getVisibility()==View.VISIBLE)" in s:
    s=re.sub(
        r'if\(addPanel\.getVisibility\(\)==View\.VISIBLE\)\{[^}]*\}',
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel || adminMode){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        s,count=1
    )

# 2) Admin Add Offer enters the same return path.
if 'findViewById(R.id.btnAdminAddOffer).setOnClickListener' not in s:
    raise SystemExit("MISSING: admin add offer listener")
s=re.sub(
    r'findViewById\\(R\\.id\\.btnAdminAddOffer\\)\\.setOnClickListener\\([^;]+;\\);',
    'findViewById(R.id.btnAdminAddOffer).setOnClickListener(v->{adminReturnToPanel=true;openAdminOfferForm();});',
    s,count=1
)
s=s.replace(
'findViewById(R.id.btnBackOffers).setOnClickListener(v->showHome());',
'findViewById(R.id.btnBackOffers).setOnClickListener(v->{if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();});',
1
)

# 3) Hardware back from add/offer also returns to admin when entered from admin.
if "if(addPanel.getVisibility()==View.VISIBLE)" in s:
    s=s.replace(
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminMode){returnToAdmin();}else showHome();return;}',
        'if(addPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        1
    )
    s=s.replace(
        'if(offersPanel.getVisibility()==View.VISIBLE){if(adminMode){returnToAdmin();}else showHome();return;}',
        'if(offersPanel.getVisibility()==View.VISIBLE){if(adminReturnToPanel){adminReturnToPanel=false;returnToAdmin();}else showHome();return;}',
        1
    )

# 4) Rating submission creates an admin review notification.
needle='db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{'
if needle not in s:
    raise SystemExit("MISSING: rating success listener")
if 'createAdminNotification("rating",rid' not in s:
    s=s.replace(
        needle,
        'db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");',
        1
    )

# 5) Complaint submission also creates the same admin review notification.
if 'db.collection("complaints").add(m).addOnSuccessListener' in s and 'createAdminNotification("complaint"' not in s:
    s=s.replace(
        'db.collection("complaints").add(m).addOnSuccessListener(x->{',
        'db.collection("complaints").add(m).addOnSuccessListener(x->{createAdminNotification("complaint","", "شكوى/اقتراح جديد","وصلت رسالة جديدة لخدمة العملاء وتحتاج متابعة.");',
        1
    )

# 6) Public contribution: add a single compact row without touching the existing visual design.
if "void installPublicContributionButtons()" not in s:
    methods=r'''    void installPublicContributionButtons(){
        if(homeStatus==null || homeStatus.getParent()==null)return;
        ViewGroup parent=(ViewGroup)homeStatus.getParent();
        if(parent.findViewWithTag("publicContributionRow")!=null)return;
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        row.setTag("publicContributionRow");
        Button suggest=btn("🏪 ضيف محلك ووسع تجارتك وخلي الناس توصلك");
        Button service=btn("💬 الشكاوى والاقتراحات");
        for(Button b:new Button[]{suggest,service}){
            b.setAllCaps(false); b.setTextSize(12); b.setMinWidth(0); b.setMinHeight(0);
            b.setPadding(dp(4),0,dp(4),0);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(52),1);
            lp.setMargins(dp(2),dp(2),dp(2),dp(2)); row.addView(b,lp);
        }
        suggest.setOnClickListener(v->showBusinessSuggestionDialog());
        service.setOnClickListener(v->show(servicePanel));
        int idx=parent.indexOfChild(homeStatus);
        parent.addView(row,Math.min(idx+1,parent.getChildCount()),new LinearLayout.LayoutParams(-1,dp(56)));
    }

    void showBusinessSuggestionDialog(){
        LinearLayout l=new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL); l.setPadding(dp(18),dp(8),dp(18),dp(6));
        EditText nm=new EditText(this); nm.setHint("اسم المنشأة / المحل *");
        Spinner cat=new Spinner(this);
        cat.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"مطاعم","محلات","عيادات","صيدليات","خدمات","أخرى"}));
        EditText ad=new EditText(this); ad.setHint("العنوان");
        EditText ph=new EditText(this); ph.setHint("رقم الهاتف (اختياري)"); ph.setInputType(3);
        EditText ds=new EditText(this); ds.setHint("وصف مختصر / الخدمات"); ds.setMinLines(3);
        l.addView(nm);l.addView(cat);l.addView(ad);l.addView(ph);l.addView(ds);
        new AlertDialog.Builder(this).setTitle("🏪 ضيف محلك ووسع تجارتك وخلي الناس توصلك")
            .setMessage("البيانات تُعرض على الإدارة للمراجعة أولًا ولن تظهر للعامة إلا بعد اعتماد الإدارة.")
            .setView(l).setPositiveButton("إرسال للإدارة",(d,w)->{
                FirebaseUser u=auth.getCurrentUser();
                if(u==null){toast("سجّل الدخول أولًا.");return;}
                String name=nm.getText().toString().trim();
                if(name.isEmpty()){toast("اكتب اسم المنشأة.");return;}
                Map<String,Object> m=new HashMap<>();
                m.put("name",name);m.put("category",cat.getSelectedItem().toString());
                m.put("address",ad.getText().toString().trim());m.put("phone",ph.getText().toString().trim());
                m.put("description",ds.getText().toString().trim());m.put("uid",u.getUid());
                m.put("status","pending");m.put("createdAt",FieldValue.serverTimestamp());
                db.collection("businessRequests").add(m).addOnSuccessListener(x->{
                    createAdminNotification("business",x.getId(),"اقتراح منشأة جديد","اقتراح منشأة جديد يحتاج مراجعة: "+name);
                    toast("✅ تم إرسال الاقتراح للإدارة.");
                }).addOnFailureListener(e->toast("تعذر إرسال الاقتراح: "+safe(e.getMessage())));
            }).setNegativeButton("إلغاء",null).show();
    }

'''
    marker="    void installBackHandler()"
    if marker not in s: raise SystemExit("MISSING: installBackHandler marker")
    s=s.replace(marker,methods+marker,1)

if "installPublicContributionButtons();" not in s:
    need("void setup(){","void setup(){\n        installPublicContributionButtons();","setup marker")

p.write_text(s,encoding="utf-8")
print("TARGETED V32 PATCH OK")
