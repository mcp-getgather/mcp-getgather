import { Card, CardContent } from "@/components/ui/card";

interface EmptyStateProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <Card className="w-full max-w-md border-0 text-center shadow-lg">
        <CardContent className="pt-8 pb-6">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <Icon className="h-8 w-8 text-gray-500" />
          </div>
          <h2 className="mb-3 text-xl font-semibold text-gray-900">{title}</h2>
          <p className="mb-6 text-gray-600">{description}</p>
          {action && action}
        </CardContent>
      </Card>
    </div>
  );
}
