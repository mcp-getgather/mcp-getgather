import BrandForm, {
  type BrandFormHandle,
  type ExtractResult,
} from "@/components/BrandForm";
import ExtractResults from "@/components/ExtractResults";
import { useRef, useState } from "react";
import { useParams } from "react-router";

export default function Start() {
  const { brandId } = useParams<{ brandId: string }>();
  const brandFormRef = useRef<BrandFormHandle>(null);
  const [extractResult, setExtractResult] = useState<ExtractResult>();

  function handleSuccess({ extractResult }: { extractResult?: ExtractResult }) {
    setExtractResult(extractResult);
  }

  return (
    <div className="space-y-6">
      <BrandForm
        brandId={brandId}
        ref={brandFormRef}
        onSuccess={handleSuccess}
        extract
      />
      <ExtractResults extractResult={extractResult} />
    </div>
  );
}
