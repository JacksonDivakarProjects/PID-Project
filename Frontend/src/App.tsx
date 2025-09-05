import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import Navigation from "@/components/Navigation";
import Home from "@/pages/Home";
import Upload from "@/pages/Upload";
import Results from "@/pages/Results";
import Review from "@/pages/Review";
import Export from "@/pages/Export";
import About from "@/pages/About";
import Playground from "@/pages/Playground";
import NotFound from "@/pages/NotFound";
import { UploadProvider } from "@/context/UploadContext"; // Import the provider

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <UploadProvider>
          <BrowserRouter>
            <div className="min-h-screen bg-background">
              <Navigation />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/results" element={<Results />} />
                <Route path="/review" element={<Review />} />
                <Route path="/export" element={<Export />} />
                <Route path="/about" element={<About />} />
                <Route path="/play-ground" element={<Playground />} />
                {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </div>
          </BrowserRouter>
        </UploadProvider>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
