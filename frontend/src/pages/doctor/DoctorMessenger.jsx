import { useSearchParams } from 'react-router-dom';
import ChatWindow from '../../components/ChatWindow';
import DoctorLayout from './DoctorLayout';
import '../../styles/messenger.css';

export default function DoctorMessenger() {
  const [searchParams] = useSearchParams();
  const initialConversationId = searchParams.get('conversationId') || '';

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Doctor-Patient Messenger</h1>
          <p>Real-time consultation messaging with your assigned patients.</p>
        </div>
      </div>
      <ChatWindow initialConversationId={initialConversationId} />
    </DoctorLayout>
  );
}
