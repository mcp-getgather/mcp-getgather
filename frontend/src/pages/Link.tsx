import BrandForm, { type BrandFormHandle } from "@/components/BrandForm";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router";

type LinkStatusResponse = {
  link_id: string;
  profile_id?: string;
  brand_id: string;
  redirect_url?: string;
  webhook?: string;
  status: "expired" | "pending";
  created_at: string;
  expires_at: string;
  message: string;
};

export default function Link() {
  const { linkId } = useParams<{ brand: string; linkId: string }>();
  const [linkData, setLinkData] = useState<LinkStatusResponse | undefined>(
    undefined,
  );

  const brandFormRef = useRef<BrandFormHandle>(null);

  async function handleUpdateLinkStatus(update: {
    status: string;
    statusMessage?: string;
    extractResult?: unknown;
    profileId?: string;
  }) {
    try {
      const response = await fetch(`/api/link/status/${linkId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: update.status,
          statusMessage: update.statusMessage,
          extractResult: update.extractResult,
          profileId: update.profileId,
        }),
      });

      if (response.status === 400) {
        const errorData = await response.json();
        if (errorData.detail && String(errorData.detail).includes("expired")) {
          brandFormRef?.current?.setView("error");
          brandFormRef?.current?.setMessage(
            "This link has expired. Please start a new authentication process.",
          );
          return;
        }
      }

      if (!response.ok) {
        console.warn(`Failed to update link status: ${response.status}`);
      }
    } catch (err) {
      console.error("Failed to update link status:", err);
    }
  }

  function handleSuccess({ profileId }: { profileId?: string }) {
    if (linkData?.redirect_url && profileId) {
      setTimeout(() => {
        window.location.href = `${linkData.redirect_url}?profile_id=${encodeURIComponent(
          profileId,
        )}`;
      }, 2000);
    } else {
      setTimeout(() => window.close(), 2000);
    }
  }

  useEffect(() => {
    const fetchLinkStatus = async () => {
      try {
        const linkResponse = await fetch(`/api/link/status/${linkId}`);
        if (linkResponse.ok) {
          const linkData = (await linkResponse.json()) as LinkStatusResponse;
          setLinkData(linkData);
          if (linkData?.status === "expired") {
            brandFormRef?.current?.setView("error");
            brandFormRef?.current?.setMessage(
              "This link has expired. Please start a new authentication process.",
            );
          }
        }
      } catch (error) {
        brandFormRef?.current?.setView("error");
        brandFormRef?.current?.setMessage(
          "Link not found. Please check the URL and try again.",
        );
        console.error("Error fetching link status:", error);
      }
    };

    fetchLinkStatus();
  }, [linkId]);

  return (
    <BrandForm
      brandId={linkData?.brand_id}
      profileId={linkData?.profile_id}
      onUpdateStatus={handleUpdateLinkStatus}
      ref={brandFormRef}
      onSuccess={handleSuccess}
      successMessage={`Authentication successful!\nYou can go back to the app now.`}
    />
  );
}
