import subprocess, sys, os, glob, json
from PIL import Image, ImageDraw
SLOT="/Volumes/Demo Take Media/aiw-builds/film-set-20261109/shared/kit/slot.sh"
FINAL="/Volumes/Demo Take Media/aiw-builds/film-set-20261109/FINAL"
OUT="/Users/willcook/src/wcook04.github.io/assets/films/loops"
TMP="/Volumes/Demo Take Media/aiw-builds/film-set-20261109/edition2/landing/tmp_loops"
os.makedirs(OUT,exist_ok=True); os.makedirs(TMP,exist_ok=True)
OVERRIDE=json.load(open(sys.argv[1])) if len(sys.argv)>1 else {}
W,H=96,54
rows=[]
for src in sorted(glob.glob(FINAL+"/*.mp4")):
    base=os.path.basename(src)[:-4]; slug=base.replace("sixty-","short-")
    dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",src]).strip())
    if slug in OVERRIDE: start=OVERRIDE[slug]
    else:
        raw=subprocess.run([SLOT,"ffmpeg","-v","error","-threads","2","-i",src,"-vf",f"fps=1,scale={W}:{H},format=gray","-f","rawvideo","-"],capture_output=True).stdout
        n=len(raw)//(W*H); fr=[raw[i*W*H:(i+1)*W*H] for i in range(n)]
        d=[0.0]+[sum(abs(a-b) for a,b in zip(fr[i][::7],fr[i-1][::7]))/(W*H/7) for i in range(1,n)]
        L=7; lo=int(dur*0.15); hi=int(dur*0.80)-L; best=None
        for s in range(lo,max(lo+1,hi)):
            w=d[s+1:s+L]
            if not w: continue
            if max(w)>28 or d[s]>28: continue     # a hard cut inside or at the start
            sc=sum(min(x,10) for x in w)
            if best is None or sc>best[0]: best=(sc,s)
        start=best[1] if best else int(dur*0.4)
    out=f"{OUT}/{slug}.mp4"
    for crf in (30,33,36):
        subprocess.run([SLOT,"ffmpeg","-v","error","-y","-threads","2","-ss",str(start),"-i",src,"-t","6.5","-an","-vf","fps=12,scale=640:360:flags=lanczos","-c:v","libx264","-preset","slow","-profile:v","main","-pix_fmt","yuv420p","-crf",str(crf),"-movflags","+faststart",out],check=True)
        if os.path.getsize(out)<240000: break
    subprocess.run(["ffmpeg","-v","error","-y","-ss","3","-i",out,"-frames:v","1",f"{TMP}/{slug}.jpg"],check=True)
    rows.append((slug,base,start,os.path.getsize(out))); print(rows[-1],flush=True)
open(os.path.dirname(TMP)+"/loops.tsv","w").write("slug\tsource\tstart_s\tbytes\n"+"".join(f"{a}\t{b}.mp4\t{c}\t{d}\n" for a,b,c,d in rows))
sheet=Image.new("RGB",(480*6,290*4),(20,16,30)); dr=ImageDraw.Draw(sheet)
for i,(slug,_,st,by) in enumerate(rows):
    im=Image.open(f"{TMP}/{slug}.jpg").resize((480,270)); x,y=(i%6)*480,(i//6)*290; sheet.paste(im,(x,y)); dr.text((x+6,y+273),f"{slug} @{st}s {by//1000}KB",fill=(240,230,210))
sheet.save(os.path.dirname(TMP)+"/loops_sheet.jpg",quality=82)
print("total",sum(r[3] for r in rows))
