import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
// Updated lucide-react imports to better match the new workflow
import { Zap, FileText, Layers , ArrowRight, FileOutput } from "lucide-react";

// Placeholder images updated to illustrate the new process
const componentIllustration = "https://placehold.co/600x400/E2E8F0/4A5568?text=1.+Component+Detection";
const ocrIllustration = "https://placehold.co/600x400/E2E8F0/4A5568?text=2.+Label+Extraction+(OCR)";
const pipelineIllustration = "https://placehold.co/600x400/E2E8F0/4A5568?text=3.+Pipeline+Detection";
const playgroundIllustration = "https://placehold.co/600x400/E2E8F0/4A5568?text=4.+Interactive+Playground";


const About = () => {
  // The workflowSteps array has been updated to reflect the new 4-step process.
  const workflowSteps = [
    {
      icon: <Zap className="h-10 w-10 text-primary" />,
      title: "Step 1: Component Detection",
      description: "Our AI scans the entire P&ID to accurately identify and locate every component—from pumps and valves to instruments and vessels—using advanced computer vision models.",
      image: componentIllustration,
    },
    {
      icon: <FileText className="h-10 w-10 text-primary" />,
      title: "Step 2: Extracting Labels via OCR",
      description: "Next, a powerful Optical Character Recognition (OCR) engine reads and digitizes all text labels, tags, and specifications, intelligently associating them with their corresponding components.",
      image: ocrIllustration,
    },
    {
      icon: <Layers className="h-10 w-10 text-primary" />,
      title: "Step 3: Pipeline Detection & Tracing",
      description: "The system traces every pipeline, identifying connection points between components and understanding the process flow. This creates a complete topological map of your system.",
      image: pipelineIllustration,
    },
    {
      icon: <Zap className="h-10 w-10 text-primary" />,
      title: "Step 4: The Playground",
      description: "All the extracted data—components, labels, and pipelines—is presented in an interactive playground. Here, you can validate the results, make adjustments, and export the structured data for your needs.",
      image: playgroundIllustration,
    }
  ];

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="bg-gradient-mesh py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl lg:text-5xl font-bold mb-4">How PIDFlow Works</h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            From a static image to a dynamic dataset, discover the intelligent process that powers our P&ID analysis engine.
          </p>
        </div>
      </section>

      {/* Workflow Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-24">
            {workflowSteps.map((step, index) => (
              <div key={index} className={`grid lg:grid-cols-2 gap-12 items-center ${index % 2 !== 0 ? 'lg:grid-flow-col-dense' : ''}`}>
                {/* Image Content */}
                <div className={`animate-fade-in ${index % 2 !== 0 ? 'lg:col-start-2' : ''}`}>
                  <Card className="overflow-hidden shadow-elegant hover:shadow-glow transition-all duration-300">
                    <img src={step.image} alt={step.title} className="w-full h-auto object-cover" />
                  </Card>
                </div>
                
                {/* Text Content */}
                <div className="space-y-4 animate-slide-in">
                  <div className="flex items-center gap-4">
                    {step.icon}
                    <h2 className="text-3xl font-bold">{step.title}</h2>
                  </div>
                  <p className="text-lg text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Final Output Section */}
      <section className="py-20 bg-card/50">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <FileOutput className="h-12 w-12 text-primary mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">The Result: Structured Digital Data</h2>
            <p className="text-xl text-muted-foreground mb-8">
                The final output is a rich, structured dataset containing all your components and their connections, ready for export and integration into your digital twin, maintenance systems, or any other engineering software.
            </p>
            <Button asChild size="xl" variant="gradient">
                <Link to="/upload">
                    Try It Yourself
                    <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
            </Button>
        </div>
      </section>
    </div>
  );
};

export default About;