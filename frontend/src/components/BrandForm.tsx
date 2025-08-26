import { Button } from "@/components/ui/button";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";

type GroupChoiceOption = { value: string; label: string };

type GroupItem =
  | {
      type: "text" | "email" | "password" | "text_multi" | "text_multi_auto";
      name: string;
      prompt: string;
    }
  | {
      type: "choice";
      name: string;
      prompt: string;
      options: GroupChoiceOption[];
    }
  | { type: "click"; name: string; prompt: string }
  | { type: "selection"; name: string; prompt: string };

type Choice = {
  name?: string;
  prompt?: string;
  groups: GroupItem[];
};

type Prompt = {
  name: string;
  prompt?: string;
  choices: Choice[];
};

type StatePayload = {
  brand_name?: string;
  error?: string | null;
  prompt?: Prompt | null;
  current_page_spec_name?: string | null;
  inputs?: Record<string, unknown>;
};

export type ExtractResult = {
  bundles: Array<{
    name: string;
    content: unknown;
    parsed?: boolean;
  }>;
};

type ActionResponse = {
  profile_id?: string;
  status: "FINISHED" | "NEED_INPUT" | "ERROR" | string;
  state: StatePayload;
  extract_result?: ExtractResult;
};

type View = "loading" | "input" | "success" | "error";

export type BrandFormHandle = {
  setView: (view: View) => void;
  setMessage: (message: string) => void;
};

type BrandFormProps = {
  brandId?: string;
  profileId?: string;
  extract?: boolean;
  onSuccess?: ({
    extractResult,
    profileId,
  }: {
    extractResult?: ExtractResult;
    profileId?: string;
  }) => void;
  onUpdateStatus?: ({
    status,
    statusMessage,
    profileId,
    extractResult,
  }: {
    status: string;
    statusMessage?: string;
    profileId?: string;
    extractResult?: unknown;
  }) => void;
};
const BrandForm = forwardRef<BrandFormHandle, BrandFormProps>(
  function BrandForm(
    {
      onUpdateStatus,
      brandId,
      onSuccess,
      profileId: profileIdProps,
      extract = false,
    }: BrandFormProps,
    ref,
  ) {
    const [view, setView] = useState<View>("loading");
    const [message, setMessage] = useState<string>("Connecting...");
    const [action, setAction] = useState<ActionResponse | null>(null);
    const [profileId, setProfileId] = useState<string | undefined>(undefined);
    const isMounted = useRef(false);

    useImperativeHandle(
      ref,
      () => ({
        setView: (nextView: View) => setView(nextView),
        setMessage: (nextMessage: string) => setMessage(nextMessage),
      }),
      [],
    );

    const brandName = useMemo(() => {
      if (action?.state?.brand_name) return action.state.brand_name;
      if (brandId) return brandId.charAt(0).toUpperCase() + brandId.slice(1);
      return "Connect Account";
    }, [brandId, action?.state?.brand_name]);

    const onImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
      const img = e.currentTarget;
      const attempted = img.dataset.fallback;
      if (!attempted || attempted === "svg") {
        img.src = img.src.replace(/\.svg$/, ".png");
        img.dataset.fallback = "png";
      } else {
        img.src = "/static/assets/logos/default.svg";
        img.onerror = null;
      }
    };

    function applyAuthResponse(nextAction: ActionResponse) {
      setAction(nextAction);
      if (nextAction.profile_id && !profileId) {
        setProfileId(profileIdProps || nextAction.profile_id);
      }

      if (nextAction.status === "FINISHED") {
        if (nextAction.state.error) {
          setView("error");
          setMessage(nextAction.state.error || "");

          onUpdateStatus?.({
            status: "error",
            statusMessage: nextAction.state.error || undefined,
          });
        } else {
          setView("success");
          setMessage(
            "Authentication successful!\nYou can go back to the app now.",
          );

          onUpdateStatus?.({
            status: "completed",
            statusMessage: nextAction.state.current_page_spec_name || undefined,
            extractResult: nextAction.extract_result,
            profileId: nextAction.profile_id,
          });
          onSuccess?.({
            extractResult: nextAction.extract_result,
            profileId: nextAction.profile_id,
          });
        }
        return;
      }

      if (nextAction.status === "ERROR") {
        const errorMsg =
          nextAction.state.error || "Error during authentication";
        setView("error");
        setMessage(errorMsg);

        onUpdateStatus?.({ status: "error", statusMessage: errorMsg });
        return;
      }

      if (nextAction.status === "NEED_INPUT") {
        setView("input");
        setMessage(nextAction.state.error || "");

        onUpdateStatus?.({
          status: "pending",
          statusMessage: nextAction.state.current_page_spec_name || undefined,
          profileId: nextAction.profile_id,
        });
        return;
      }

      setView("loading");
      setMessage("Loading...");

      onUpdateStatus?.({
        status: "pending",
        statusMessage: nextAction.state.current_page_spec_name || undefined,
      });
      setTimeout(() => authenticateNext(nextAction.state), 0);
    }

    async function authenticateNext(actionState?: StatePayload) {
      try {
        const response = await fetch(`/api/auth/v1/${brandId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            profile_id: profileIdProps || profileId,
            state: actionState
              ? {
                  current_page_spec_name: actionState?.current_page_spec_name,
                  inputs: actionState?.inputs,
                }
              : null,
            extract,
          }),
        });

        if (
          response.status === 503 &&
          response.headers.get("X-No-Retry") === "true"
        ) {
          const errorData = await response.json();
          setView("error");
          setMessage(
            errorData.detail ||
              "Browser startup failed. Please try again later.",
          );
          return;
        }

        if (response.status === 422) {
          const errorData = await response.json();
          const errorMsg =
            errorData.detail?.[0]?.msg || "Invalid brand or parameters";
          setView("error");
          setMessage(`Configuration error: ${errorMsg}`);
          return;
        }

        if (!response.ok) {
          const errorText = await response.text();
          setView("error");
          setMessage(
            `HTTP ${response.status}: ${errorText || "Unknown error"}`,
          );
          return;
        }

        const nextAction = (await response.json()) as ActionResponse;
        applyAuthResponse(nextAction);
      } catch (error) {
        console.error("Error in auth flow:", error);
        setView("error");
        setMessage(`Error during authentication: ${(error as Error).message}`);
      }
    }

    useEffect(() => {
      setView("loading");
      setMessage("Connecting...");
      if (brandId && !isMounted.current) {
        isMounted.current = true;
        authenticateNext();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [brandId]);

    const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      const form = e.currentTarget;
      const formData = new FormData(form);

      const submitter = (e.nativeEvent as SubmitEvent).submitter as
        | HTMLButtonElement
        | undefined;
      if (submitter?.name) {
        formData.append(submitter.name, submitter.value || "true");
      }
      const data = Object.fromEntries(formData.entries());

      setView("loading");
      setMessage("Submitting...");
      const newState = {
        ...action?.state,
        inputs: { ...action?.state?.inputs, ...data },
      };

      setAction((prev) =>
        prev
          ? {
              ...prev,
              state: newState,
            }
          : prev,
      );

      authenticateNext(newState);
    };

    const renderGroupItem = (item: GroupItem, idx: number) => {
      switch (item.type) {
        case "text":
        case "email":
        case "password":
        case "text_multi":
        case "text_multi_auto":
          return (
            <div key={idx} className="mb-3">
              <label
                htmlFor={item.name}
                className="block text-slate-700 font-medium mb-1"
              >
                {item.prompt}
              </label>
              <input
                id={item.name}
                name={item.name}
                type={item.type}
                required
                data-testid={`input-${item.name}`}
                className="w-full rounded-md border border-slate-300 bg-slate-50 px-3 py-2"
              />
            </div>
          );
        case "choice":
          return (
            <div key={idx} className="mb-3">
              <label className="block text-slate-700 font-medium mb-2">
                {item.prompt}
              </label>
              <div className="flex gap-4 flex-wrap">
                {item.options.map((opt) => {
                  const id = `${item.name}-${opt.value}`;
                  return (
                    <div key={id} className="inline-flex items-center gap-2">
                      <input
                        id={id}
                        type="radio"
                        name={item.name}
                        value={opt.value}
                        data-testid={`choice-${item.name}-${opt.value}`}
                      />
                      <label htmlFor={id}>{opt.label}</label>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        case "click":
        case "selection":
          return (
            <Button
              key={idx}
              className="w-full text-white rounded-md px-4 py-2"
              type="submit"
              name={item.name}
              value="true"
              data-testid={`button-${item.name}`}
            >
              {item.prompt}
            </Button>
          );
        default:
          return null;
      }
    };

    return (
      <div className="bg-slate-50 py-8 px-4">
        <main className="max-w-md mx-auto">
          <div className="bg-white border rounded-xl shadow-sm p-8 mt-6">
            <div className="text-center mb-6">
              {brandId && (
                <img
                  className="w-12 h-12 object-contain mx-auto rounded-lg bg-slate-100 p-2"
                  src={`/static/assets/logos/${brandId}.svg`}
                  alt={brandId}
                  onError={onImageError}
                  data-fallback="svg"
                />
              )}
              <h1 className="text-xl font-semibold text-slate-800">
                {brandName}
              </h1>
            </div>

            {!!message && (!action?.state?.prompt || !action?.state?.error) && (
              <p
                className="text-center text-slate-500 mb-4 whitespace-pre-line"
                data-testid="progress"
              >
                {message}
              </p>
            )}

            {view === "input" && action?.state?.prompt && (
              <section id="forms">
                {action.state.prompt.prompt && (
                  <>
                    <label className="block text-slate-700 font-medium mb-1">
                      {action.state.prompt.prompt}
                    </label>
                    <hr className="my-3" />
                  </>
                )}

                {action.state.prompt.choices.map((choice, index) => (
                  <div key={choice.name || Math.random()} className="mb-0">
                    {action.state.error && (
                      <div
                        className="text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-2"
                        data-testid="error-message"
                      >
                        {action.state.error}
                      </div>
                    )}

                    <form
                      onSubmit={(e) => handleFormSubmit(e)}
                      data-testid={`form-${choice.name}`}
                    >
                      {choice.groups.map((g, idx) =>
                        renderGroupItem(g as GroupItem, idx),
                      )}
                      {/* If there are no click/button type, render a submit button */}
                      {choice.groups.every(
                        (group) => group.type !== "click",
                      ) && (
                        <Button
                          className="w-full text-white rounded-md px-4 py-2"
                          type="submit"
                          name="submit"
                          value="true"
                          data-testid="submit-button"
                        >
                          Continue
                        </Button>
                      )}
                    </form>
                    {action.state.prompt &&
                      action.state.prompt.choices?.length > 1 &&
                      index !== action.state.prompt.choices.length - 1 && (
                        <hr className="mt-3" />
                      )}
                  </div>
                ))}
              </section>
            )}
          </div>
        </main>
      </div>
    );
  },
);

export default BrandForm;
