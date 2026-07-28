import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, type DragEvent } from "react";
import { UploadCloud, ImageIcon, X, Loader2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/upload")({
  head: () => ({
    meta: [{ title: "Upload chart — TradeVision AI" }],
  }),
  component: UploadPage,
});

const MAX_SIZE = 8 * 1024 * 1024;
const ACCEPTED = ["image/png", "image/jpeg", "image/webp"];

function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [processing, setProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFiles = (files: FileList | null) => {
    if (!files || !files[0]) return;
    const f = files[0];
    if (!ACCEPTED.includes(f.type)) {
      toast.error("Unsupported file", {
        description: "Upload a PNG, JPEG, or WEBP image.",
      });
      return;
    }
    if (f.size > MAX_SIZE) {
      toast.error("File too large", { description: "Max 8 MB." });
      return;
    }
    setFile(f);
  };

  const onDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const analyze = async () => {
    if (!file) return;
    setProcessing(true);
    // Backend analysis endpoint is not built yet.
    // Show a real loading state, then a "processing" placeholder — never fabricate results.
    await new Promise((r) => setTimeout(r, 1600));
    setProcessing(false);
    toast("Analysis engine coming soon", {
      description:
        "The OCR + technical analysis pipeline is under construction. Your upload was accepted for preview.",
    });
  };

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Analysis"
        title="Upload a chart"
        description="Drop a TradingView screenshot below. TradeVision will read the indicators and produce an explainable report."
      />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <label
            htmlFor="file-input"
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`glass-panel flex min-h-[320px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
              dragOver
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/60"
            }`}
          >
            {preview ? (
              <div className="relative w-full">
                <img
                  src={preview}
                  alt="Chart preview"
                  className="mx-auto max-h-[420px] w-auto rounded-lg border border-border"
                />
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    setFile(null);
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                  className="absolute right-2 top-2 rounded-md border border-border bg-background/80 p-1.5 text-muted-foreground backdrop-blur hover:text-foreground"
                  aria-label="Remove image"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <>
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 text-primary">
                  <UploadCloud className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <p className="text-base font-medium text-foreground">
                  Drop your chart here
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  or click to browse — PNG, JPEG, WEBP · max 8 MB
                </p>
              </>
            )}
            <input
              id="file-input"
              ref={inputRef}
              type="file"
              className="sr-only"
              accept={ACCEPTED.join(",")}
              onChange={(e) => handleFiles(e.target.files)}
            />
          </label>

          {file ? (
            <div className="mt-4 flex items-center justify-between rounded-lg border border-border bg-panel/40 px-4 py-3">
              <div className="flex min-w-0 items-center gap-3">
                <ImageIcon className="h-4 w-4 shrink-0 text-primary" />
                <div className="min-w-0">
                  <p className="truncate text-sm text-foreground">{file.name}</p>
                  <p className="font-mono text-[11px] text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB · {file.type.replace("image/", "").toUpperCase()}
                  </p>
                </div>
              </div>
              <Button onClick={analyze} disabled={processing}>
                {processing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing…
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-1.5 h-4 w-4" />
                    Analyze
                  </>
                )}
              </Button>
            </div>
          ) : null}
        </div>

        <aside className="space-y-4">
          <div className="glass-panel rounded-xl p-5">
            <p className="font-mono text-[11px] uppercase tracking-widest text-primary">
              What we look at
            </p>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li>· Candle structure & recent price action</li>
              <li>· Moving averages (EMA, SMA)</li>
              <li>· Momentum indicators (RSI, MACD)</li>
              <li>· Volume confluence</li>
              <li>· Key support / resistance zones</li>
            </ul>
          </div>

          {processing || file ? (
            <div className="glass-panel rounded-xl p-5">
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Analysis preview
              </p>
              {processing ? (
                <div className="mt-3 space-y-3">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : (
                <p className="mt-3 text-sm text-muted-foreground">
                  Click <span className="text-foreground">Analyze</span> to queue this chart for the reasoning engine.
                </p>
              )}
            </div>
          ) : null}

          <div className="rounded-xl border border-warning/30 bg-warning/5 p-4">
            <p className="text-xs text-muted-foreground">
              <span className="font-mono uppercase tracking-wider text-warning">
                Note ·{" "}
              </span>
              Analysis output is educational. TradeVision does not place trades and is not financial advice.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
