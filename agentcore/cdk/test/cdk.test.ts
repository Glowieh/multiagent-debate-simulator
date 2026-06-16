import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { type AgentCoreProjectSpec } from '@aws/agentcore-cdk';
import { AgentCoreStack } from '../lib/cdk-stack';

const emptySpec = {
  name: 'testproject',
  version: 1,
  managedBy: 'CDK' as const,
  runtimes: [],
  memories: [],
  credentials: [],
  evaluators: [],
  onlineEvalConfigs: [],
  policyEngines: [],
  payments: [],
  configBundles: [],
  agentCoreGateways: [],
  mcpRuntimeTools: [],
  unassignedTargets: [],
  datasets: [],
};

test('AgentCoreStack synthesizes with empty spec', () => {
  const app = new cdk.App();
  const stack = new AgentCoreStack(app, 'TestStack', {
    spec: emptySpec,
  });
  const template = Template.fromStack(stack);
  template.hasOutput('StackNameOutput', {
    Description: 'Name of the CloudFormation Stack',
  });
});

test('AgentCoreStack creates LangSmith secret for runtime agent', () => {
  const app = new cdk.App();
  const stack = new AgentCoreStack(app, 'DebateAgentStack', {
    spec: {
      ...emptySpec,
      name: 'DebateAgent',
      runtimes: [
        {
          name: 'DebateAgent',
          build: 'CodeZip',
          entrypoint: 'main.py',
          codeLocation: 'app/DebateAgent/',
          runtimeVersion: 'PYTHON_3_12',
          networkMode: 'PUBLIC',
          protocol: 'HTTP',
        },
      ],
    } as unknown as AgentCoreProjectSpec,
    langsmithProject: 'my-langsmith-project',
  });
  const template = Template.fromStack(stack);

  template.resourceCountIs('AWS::SecretsManager::Secret', 1);
  template.hasOutput('LangSmithSecretArnDebateAgent', {});
});
