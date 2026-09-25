from pathlib import Path
p=Path("app/src/main/java/com/negmdiarb/app/MainActivity.java")
s=p.read_text(encoding="utf-8")

def need(old,new,label):
    global s
    if old not in s: raise SystemExit("MISSING: "+label)
    s=s.replace(old,new,1)

# Performance: smaller mobile result sets and lighter image rendering.
s=s.replace('.whereEqualTo("status","approved").whereEqualTo("active",true).limit(200).get()',
            '.whereEqualTo("status","approved").whereEqualTo("active",true).limit(60).get()')
s=s.replace('.whereEqualTo("status","approved").whereEqualTo("active",true).whereEqualTo("featured",true).limit(100).get()',
            '.whereEqualTo("status","approved").whereEqualTo("active",true).whereEqualTo("featured",true).limit(40).get()')
s=s.replace('db.collection("businesses").limit(300).get()','db.collection("businesses").limit(150).get()')
s=s.replace('db.collection("offers").limit(300).get()','db.collection("offers").limit(150).get()')
s=s.replace('db.collection("complaints").limit(300).get()','db.collection("complaints").limit(150).get()')
s=s.replace('db.collection("ratings").limit(300).get()','db.collection("ratings").limit(150).get()')
s=s.replace('Glide.with(this).load(String.valueOf(o)).centerCrop().into(iv);',
            'Glide.with(this).load(String.valueOf(o)).override(dp(340),dp(260)).centerCrop().into(iv);')

# Needed imports for compressed image fallback.
need('import android.graphics.Color;',
     'import android.graphics.Color;\nimport android.graphics.Bitmap;\nimport android.graphics.BitmapFactory;',
     'bitmap imports')
need('import java.io.File;',
     'import java.io.File;\nimport java.io.ByteArrayOutputStream;\nimport java.io.InputStream;\nimport java.util.concurrent.Executors;',
     'image io imports')

# Ratings carry the real business name, avoiding one Firestore read per rating in the admin screen.
need('String rid=u.getUid()+"_"+bid; Map<String,Object>m=new HashMap<>(); m.put("businessId",bid); m.put("stars",selected[0]);',
     'String rid=u.getUid()+"_"+bid; Map<String,Object>m=new HashMap<>(); m.put("businessId",bid); m.put("businessName",""); m.put("stars",selected[0]);',
     'rating map')
need('db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();}).addOnFailureListener(e->hint.setText("تعذر إرسال التقييم. جرّب مرة أخرى."));',
     'db.collection("businesses").document(bid).get().addOnSuccessListener(bd->{m.put("businessName",safe(bd.getString("name")));db.collection("ratings").document(rid).set(m).addOnSuccessListener(q->{createAdminNotification("rating",rid,"تقييم جديد","يوجد تقييم جديد يحتاج مراجعة.");toast("✅ تم إرسال تقييمك للمراجعة");dialog.dismiss();}).addOnFailureListener(e->hint.setText("تعذر إرسال التقييم. جرّب مرة أخرى."));}).addOnFailureListener(e->hint.setText("تعذر قراءة اسم المنشأة. جرّب مرة أخرى."));',
     'rating save')
s=s.replace('if(!bid.isEmpty())db.collection("businesses").document(bid).get().addOnSuccessListener(bs->{String real=safe(bs.getString("name"));if(!real.isEmpty())h.setText("🏪 "+real);});',
            'if(saved.isEmpty()&&!bid.isEmpty())db.collection("businesses").document(bid).get().addOnSuccessListener(bs->{String real=safe(bs.getString("name"));if(!real.isEmpty())h.setText("🏪 "+real);});',1)

# Complaints badge.
s=s.replace('String[][] q={{"changeRequests","status","pending","طلبات",String.valueOf(R.id.btnAdminRequests)},{"offers","status","pending","عروض",String.valueOf(R.id.btnAdminOffers)},{"ratings","status","pending","تقييمات",String.valueOf(R.id.btnAdminRatings)}};',
            'String[][] q={{"changeRequests","status","pending","طلبات",String.valueOf(R.id.btnAdminRequests)},{"offers","status","pending","عروض",String.valueOf(R.id.btnAdminOffers)},{"ratings","status","pending","تقييمات",String.valueOf(R.id.btnAdminRatings)},{"complaints","status","open","شكاوى",String.valueOf(R.id.btnAdminComplaints)}};',1)

# Owner edits can carry photos to the admin approval request.
need('Map<String,Object>changes=businessFields(false);Map<String,Object>req=new HashMap<>();req.put("businessId",bid);req.put("ownerUid",u.getUid());req.put("changes",changes);req.put("status","pending");req.put("createdAt",FieldValue.serverTimestamp());addStatus.setText("☁️ جاري إرسال التعديل للمراجعة...");db.collection("changeRequests").add(req).addOnSuccessListener(x->addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.")).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));',
     'Map<String,Object>changes=businessFields(false); addStatus.setText(imageUris.isEmpty()?"☁️ جاري إرسال التعديل للمراجعة...":"🖼️ جاري تجهيز الصور ثم إرسال التعديل للمراجعة..."); encodeImagesForFirestoreAsync().addOnSuccessListener(imgs->{if(!imgs.isEmpty())changes.put("imageDataUrls",imgs);Map<String,Object>req=new HashMap<>();req.put("businessId",bid);req.put("ownerUid",u.getUid());req.put("changes",changes);req.put("status","pending");req.put("createdAt",FieldValue.serverTimestamp());db.collection("changeRequests").add(req).addOnSuccessListener(x->{imageUris.clear();renderThumbs();addStatus.setText("✅ تم إرسال التعديل للإدارة. لن يظهر للعامة إلا بعد الموافقة.");}).addOnFailureListener(e->addStatus.setText("❌ تعذر إرسال الطلب: "+safe(e.getMessage())));}).addOnFailureListener(e->addStatus.setText("❌ تعذر تجهيز الصور: "+safe(e.getMessage())));',
     'owner image request')

# If Firebase Storage is unavailable, persist compressed small images in Firestore.
need('saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");\n                    addStatus.setText("✅ تم حفظ بيانات المنشأة، لكن رفع الصور تعذر. يمكنك الضغط على حفظ مرة أخرى لإعادة المحاولة.\\n"+storageErrorMessage(e));',
     'addStatus.setText("⚠️ التخزين السحابي للصور غير متاح، جاري حفظ نسخة صور مضغوطة داخل Firestore..."); encodeImagesForFirestoreAsync().addOnSuccessListener(imgs->{HashMap<String,Object> p=new HashMap<>();p.put("imageDataUrls",imgs);db.collection("businesses").document(id).set(p,SetOptions.merge()).addOnSuccessListener(z->{imageUris.clear();renderThumbs();finishBusinessSave(saveBtn,"✅ تم حفظ المنشأة والصور على السحابة.");}).addOnFailureListener(x->{saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");addStatus.setText("❌ تعذر حفظ الصور: "+safe(x.getMessage()));});}).addOnFailureListener(x->{saveBtn.setEnabled(true);saveBtn.setText("💾 حفظ البيانات");addStatus.setText("❌ تعذر تجهيز الصور: "+safe(x.getMessage()));});',
     'storage fallback')

# Display Firestore fallback images when imageUrls is empty.
need('Object imgsObj=d.get("imageUrls");\n        if(imgsObj instanceof List){',
     'Object imgsObj=d.get("imageUrls"); if(!(imgsObj instanceof List)||((List<?>)imgsObj).isEmpty())imgsObj=d.get("imageDataUrls");\n        if(imgsObj instanceof List){',
     'image display fallback')

# Async image compression: max 4 images, max side ~1280, JPEG quality 58.
marker='    void runOcr(Uri u)'
if marker not in s: raise SystemExit("MISSING: runOcr marker")
helpers='''    Task<List<String>> encodeImagesForFirestoreAsync(){
        ArrayList<Uri> copy=new ArrayList<>(imageUris);
        if(copy.isEmpty())return Tasks.forResult(new ArrayList<>());
        return Tasks.call(Executors.newSingleThreadExecutor(),()->{
            ArrayList<String> out=new ArrayList<>();
            int max=Math.min(copy.size(),4);
            for(int i=0;i<max;i++){
                String data=encodeImageDataUrl(copy.get(i));
                if(data!=null&&!data.isEmpty())out.add(data);
            }
            return out;
        });
    }

    String encodeImageDataUrl(Uri uri)throws Exception{
        if(uri==null)return "";
        android.content.ContentResolver cr=getContentResolver();
        BitmapFactory.Options bounds=new BitmapFactory.Options();
        bounds.inJustDecodeBounds=true;
        InputStream a=cr.openInputStream(uri);
        if(a==null)return "";
        BitmapFactory.decodeStream(a,null,bounds);
        a.close();
        int maxSide=Math.max(bounds.outWidth,bounds.outHeight),sample=1;
        while(maxSide/(sample*2)>1280)sample*=2;
        BitmapFactory.Options opts=new BitmapFactory.Options();
        opts.inSampleSize=Math.max(1,sample);
        opts.inPreferredConfig=Bitmap.Config.RGB_565;
        InputStream b=cr.openInputStream(uri);
        if(b==null)return "";
        Bitmap bmp=BitmapFactory.decodeStream(b,null,opts);
        b.close();
        if(bmp==null)return "";
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG,58,out);
        bmp.recycle();
        return "data:image/jpeg;base64,"+android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP);
    }

'''
s=s.replace(marker,helpers+marker,1)

p.write_text(s,encoding="utf-8")
print("V33 PATCH OK")
