import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { Check, Copy } from 'lucide-react';

interface MarkdownBlockProps {
  content: string;
}

const CodeBlock = ({
  language,
  children,
}: {
  language: string;
  children: string;
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={handleCopy}
        style={{
          position: 'absolute',
          right: 8,
          top: 8,
          background: 'rgba(255,255,255,0.1)',
          border: 'none',
          borderRadius: 4,
          padding: 4,
          color: '#fff',
          cursor: 'pointer',
          zIndex: 10,
        }}
        title="Copy code"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
      <SyntaxHighlighter style={vscDarkPlus} language={language} PreTag="div">
        {children}
      </SyntaxHighlighter>
    </div>
  );
};

export const MarkdownBlock: React.FC<MarkdownBlockProps> = ({ content }) => {
  return (
    <div className="prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const codeText = String(children).replace(/\n$/, '');

            return !inline && match ? (
              <CodeBlock language={match[1]}>{codeText}</CodeBlock>
            ) : (
              <code {...props} className={className}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
