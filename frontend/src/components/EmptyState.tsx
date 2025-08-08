import { Card, CardContent } from "@/components/ui/card";

interface EmptyStateProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Card className="max-w-md w-full text-center border-0 shadow-lg">
        <CardContent className="pt-8 pb-6">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Icon className="w-8 h-8 text-gray-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">{title}</h2>
          <p className="text-gray-600 mb-6">{description}</p>
          {action && action}
        </CardContent>
      </Card>
    </div>
  );
}
