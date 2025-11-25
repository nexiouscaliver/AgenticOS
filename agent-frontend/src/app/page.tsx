import { DocumentUploader } from "@/components/document-uploader";
import { ChatInterface } from "@/components/chat-interface";
import { Toaster } from "@/components/ui/sonner";

export default function Home() {
  return (
    <main className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Multi-Modal RAG System</h1>
          <p className="text-muted-foreground">
            Upload documents (PDF, Images, Data) and chat with them using Gemini Flash 2.5
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1 space-y-6">
            <DocumentUploader />

            <div className="p-4 rounded-lg bg-muted/50 text-sm space-y-2">
              <h3 className="font-semibold">System Status</h3>
              <div className="flex justify-between">
                <span>Backend</span>
                <span className="text-green-500">● Online</span>
              </div>
              <div className="flex justify-between">
                <span>Vector DB</span>
                <span className="text-green-500">● Connected</span>
              </div>
              <div className="flex justify-between">
                <span>Model</span>
                <span className="text-blue-500">Gemini Flash 2.5</span>
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            <ChatInterface />
          </div>
        </div>
      </div>
      <Toaster />
    </main>
  );
}
